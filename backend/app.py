from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from config import Config
from agents.retrieval_agent import RetrievalAgent
from agents.analysis_agent import AnalysisAgent
from agents.voice_agent import VoiceAgent
from mcp.plant_db import PlantDatabase
from utils.session_manager import SessionManager
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080", "null"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize components
retrieval_agent = RetrievalAgent()
analysis_agent = AnalysisAgent()
voice_agent = VoiceAgent()
plant_db = PlantDatabase()
session_manager = SessionManager(timeout_seconds=Config.SESSION_TIMEOUT)

# Initialize on startup (Flask 3.0 compatible)
def initialize():
    """Initialize the application"""
    print("Initializing Tata Steel Virtual Assistant...")
    
    # Create necessary directories
    os.makedirs(Config.SOPS_DIR, exist_ok=True)
    os.makedirs(Config.VECTOR_DB_DIR, exist_ok=True)
    
    # Load SOPs if available
    try:
        retrieval_agent.load_sops_from_directory()
        print("SOPs loaded successfully")
    except Exception as e:
        print(f"Error loading SOPs: {e}")
    
    print("Initialization complete")

# Call initialization immediately
initialize()


# ====================
# SESSION ENDPOINTS
# ====================

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new session"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    session_id = session_manager.create_session(user_id)
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'message': 'Session created successfully'
    })


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    session = session_manager.get_session(session_id)
    
    if session:
        return jsonify({
            'success': True,
            'session': {
                'id': session['id'],
                'created_at': session['created_at'].isoformat(),
                'last_activity': session['last_activity'].isoformat(),
                'message_count': len(session['conversation_history'])
            }
        })
    
    return jsonify({
        'success': False,
        'error': 'Session not found or expired'
    }), 404


@app.route('/api/session/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """Get conversation history for a session"""
    last_n = request.args.get('last_n', type=int)
    
    history = session_manager.get_conversation_history(session_id, last_n)
    
    return jsonify({
        'success': True,
        'history': history
    })


# ====================
# CHAT ENDPOINTS
# ====================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint - orchestrates all agents
    """
    data = request.json
    
    if not data or 'message' not in data:
        return jsonify({
            'success': False,
            'error': 'Message is required'
        }), 400
    
    session_id = data.get('session_id')
    message = data.get('message')
    include_plant_data = data.get('include_plant_data', False)
    
    # Create session if not provided
    if not session_id:
        session_id = session_manager.create_session()
    
    # Verify session exists
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Invalid or expired session'
        }), 404
    
    try:
        # Step 1: Retrieve relevant SOPs using RAG
        print(f"Query: {message}")
        sop_context = retrieval_agent.get_context_for_query(message)
        
        # Step 2: Check if query mentions specific equipment
        equipment_context = ""
        if include_plant_data:
            equipment_context = _get_equipment_context(message)
        
        # Step 3: Combine contexts
        full_context = sop_context
        if equipment_context:
            full_context += f"\n\nCurrent Plant Data:\n{equipment_context}"
        
        # Step 4: Get conversation history for context
        conversation_history = session_manager.get_conversation_history(session_id, last_n=4)
        
        # Step 5: Generate response using Analysis Agent
        response = analysis_agent.analyze_with_context(
            query=message,
            context=full_context,
            conversation_history=conversation_history
        )
        
        # Step 6: Save to session
        session_manager.add_message(session_id, 'user', message)
        session_manager.add_message(session_id, 'assistant', response, {
            'included_plant_data': include_plant_data
        })
        
        return jsonify({
            'success': True,
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500


def _get_equipment_context(query: str) -> str:
    """Extract equipment information if mentioned in query"""
    query_lower = query.lower()
    context_parts = []
    
    # Search for equipment mentioned in query
    equipment_results = plant_db.search_equipment(query)
    
    if equipment_results:
        for equipment in equipment_results[:2]:  # Limit to 2 most relevant
            eq_id = equipment['id']
            
            # Get current status
            status = plant_db.check_equipment_status(eq_id)
            context_parts.append(f"Equipment: {equipment['name']} ({eq_id})")
            context_parts.append(f"Status: {status['status']}")
            context_parts.append(f"Location: {equipment['location']}")
            
            if status['sensor_data']:
                context_parts.append(f"Temperature: {status['sensor_data']['temperature']:.1f}°C")
                context_parts.append(f"Vibration: {status['sensor_data']['vibration']:.2f} mm/s")
            
            if status['alerts']:
                context_parts.append("Active Alerts:")
                for alert in status['alerts']:
                    context_parts.append(f"  - {alert['message']} ({alert['severity']})")
            
            context_parts.append("")
    
    return "\n".join(context_parts)


# ====================
# PREDICTION ENDPOINTS
# ====================

@app.route('/api/predict/issue', methods=['POST'])
def predict_issue():
    """Predict equipment issue based on symptoms"""
    data = request.json
    
    if not data or 'symptoms' not in data:
        return jsonify({
            'success': False,
            'error': 'Symptoms are required'
        }), 400
    
    equipment_id = data.get('equipment_id')
    symptoms = data.get('symptoms')
    
    # Add plant data if equipment ID provided
    if equipment_id:
        equipment_info = plant_db.get_equipment_info(equipment_id)
        sensor_data = plant_db.get_sensor_data(equipment_id)
        
        if equipment_info and sensor_data:
            symptoms['equipment_name'] = equipment_info['name']
            symptoms['current_temperature'] = sensor_data['temperature']
            symptoms['current_vibration'] = sensor_data['vibration']
    
    # Get prediction from Analysis Agent
    prediction = analysis_agent.predict_issue(symptoms)
    
    return jsonify({
        'success': True,
        'prediction': prediction,
        'timestamp': datetime.now().isoformat()
    })


# ====================
# EQUIPMENT ENDPOINTS
# ====================

@app.route('/api/equipment', methods=['GET'])
def get_all_equipment():
    """Get list of all equipment"""
    equipment = plant_db.get_all_equipment()
    
    return jsonify({
        'success': True,
        'equipment': equipment,
        'count': len(equipment)
    })


@app.route('/api/equipment/<equipment_id>', methods=['GET'])
def get_equipment_details(equipment_id):
    """Get detailed information about specific equipment"""
    equipment_info = plant_db.get_equipment_info(equipment_id)
    
    if not equipment_info:
        return jsonify({
            'success': False,
            'error': 'Equipment not found'
        }), 404
    
    sensor_data = plant_db.get_sensor_data(equipment_id)
    status = plant_db.check_equipment_status(equipment_id)
    maintenance_history = plant_db.get_maintenance_history(equipment_id)
    
    return jsonify({
        'success': True,
        'equipment': {
            'id': equipment_id,
            'info': equipment_info,
            'sensor_data': sensor_data,
            'status': status,
            'maintenance_history': maintenance_history
        }
    })


@app.route('/api/equipment/<equipment_id>/sensor-data', methods=['GET'])
def get_sensor_data(equipment_id):
    """Get real-time sensor data for equipment"""
    sensor_data = plant_db.get_sensor_data(equipment_id)
    
    if not sensor_data:
        return jsonify({
            'success': False,
            'error': 'Equipment not found'
        }), 404
    
    return jsonify({
        'success': True,
        'equipment_id': equipment_id,
        'sensor_data': sensor_data
    })


@app.route('/api/equipment/<equipment_id>/maintenance-history', methods=['GET'])
def get_maintenance_history(equipment_id):
    """Get maintenance history for equipment"""
    days = request.args.get('days', default=30, type=int)
    history = plant_db.get_maintenance_history(equipment_id, days)
    
    return jsonify({
        'success': True,
        'equipment_id': equipment_id,
        'history': history,
        'count': len(history)
    })


@app.route('/api/equipment/<equipment_id>/faults', methods=['GET'])
def get_fault_history(equipment_id):
    """Get fault history for equipment"""
    days = request.args.get('days', default=90, type=int)
    faults = plant_db.get_fault_history(equipment_id, days)
    
    return jsonify({
        'success': True,
        'equipment_id': equipment_id,
        'faults': faults,
        'count': len(faults)
    })


@app.route('/api/equipment/search', methods=['GET'])
def search_equipment():
    """Search equipment by query"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter q is required'
        }), 400
    
    results = plant_db.search_equipment(query)
    
    return jsonify({
        'success': True,
        'results': results,
        'count': len(results)
    })


# ====================
# VOICE ENDPOINTS
# ====================

@app.route('/api/voice/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert speech to text"""
    if 'audio' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No audio file provided'
        }), 400
    
    audio_file = request.files['audio']
    
    # Save temporarily
    temp_path = os.path.join(Config.DATA_DIR, 'temp_audio.wav')
    audio_file.save(temp_path)
    
    try:
        result = voice_agent.speech_to_text(audio_file_path=temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            'success': result.get('success', False),
            'text': result.get('text', ''),
            'error': result.get('error')
        })
    
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/voice/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({
            'success': False,
            'error': 'Text is required'
        }), 400
    
    text = data['text']
    lang = data.get('lang', 'en')
    slow = data.get('slow', False)
    
    result = voice_agent.text_to_speech(text, lang, slow)
    
    if result.get('success'):
        return jsonify({
            'success': True,
            'audio_base64': result['audio_base64'],
            'format': result['format']
        })
    
    return jsonify({
        'success': False,
        'error': result.get('error', 'Unknown error')
    }), 500


@app.route('/api/voice/supported-languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages for TTS"""
    languages = voice_agent.get_supported_languages()
    
    return jsonify({
        'success': True,
        'languages': languages
    })


# ====================
# SOP MANAGEMENT ENDPOINTS
# ====================

@app.route('/api/sops/upload', methods=['POST'])
def upload_sop():
    """Upload SOP document"""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected'
        }), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Only PDF files are supported'
        }), 400
    
    try:
        # Save file
        filepath = os.path.join(Config.SOPS_DIR, file.filename)
        file.save(filepath)
        
        # Reload SOPs
        retrieval_agent.load_sops_from_directory()
        
        return jsonify({
            'success': True,
            'message': f'SOP {file.filename} uploaded successfully',
            'filename': file.filename
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sops/reload', methods=['POST'])
def reload_sops():
    """Reload all SOPs from directory"""
    try:
        retrieval_agent.load_sops_from_directory()
        count = retrieval_agent.vector_store.get_collection_count()
        
        return jsonify({
            'success': True,
            'message': 'SOPs reloaded successfully',
            'document_count': count
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sops/count', methods=['GET'])
def get_sop_count():
    """Get count of loaded SOP documents"""
    count = retrieval_agent.vector_store.get_collection_count()
    
    return jsonify({
        'success': True,
        'document_count': count
    })


# ====================
# UTILITY ENDPOINTS
# ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'retrieval_agent': retrieval_agent.vector_store.get_collection_count() >= 0,
            'analysis_agent': Config.GEMINI_API_KEY is not None,
            'voice_agent': True,
            'plant_db': True
        },
        'active_sessions': session_manager.get_active_sessions_count()
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    return jsonify({
        'success': True,
        'stats': {
            'active_sessions': session_manager.get_active_sessions_count(),
            'sop_documents': retrieval_agent.vector_store.get_collection_count(),
            'equipment_count': len(plant_db.get_all_equipment()),
            'uptime': 'N/A'
        }
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )