import google.generativeai as genai
from config import Config
from typing import Dict, List, Optional

class AnalysisAgent:
    """Uses Gemini to analyze queries and provide insights"""
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Use correct Gemini model name (updated for latest API)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # System prompt for maintenance context
        self.system_context = """You are an expert maintenance assistant for Tata Steel.
Your role is to help engineers and technicians with:
- Equipment troubleshooting and fault diagnosis
- Maintenance procedures and SOPs
- Predictive maintenance insights
- Safety guidelines and best practices

Always provide:
1. Clear, actionable steps
2. Safety warnings where relevant
3. Reference to specific SOP sections when available
4. Root cause analysis for faults

Be concise but thorough. Use technical terminology appropriate for maintenance engineers."""
    
    def analyze_with_context(self, query: str, context: str, conversation_history: List[Dict] = None) -> str:
        """
        Analyze query with retrieved SOP context
        
        Args:
            query: User's question
            context: Retrieved SOP information from RAG
            conversation_history: Previous messages for context
        """
        # Build the prompt
        prompt = self._build_prompt(query, context, conversation_history)
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            print(f"Gemini API error: {e}")
            return f"I encountered an error analyzing your query. Please try rephrasing or contact support. Error: {str(e)}"
    
    def _build_prompt(self, query: str, context: str, conversation_history: List[Dict] = None) -> str:
        """Construct the full prompt for Gemini"""
        
        prompt_parts = [self.system_context, "\n\n"]
        
        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("Previous conversation:\n")
            for msg in conversation_history[-3:]:  # Last 3 exchanges
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role.upper()}: {content}\n")
            prompt_parts.append("\n")
        
        # Add retrieved context
        prompt_parts.append(f"{context}\n\n")
        
        # Add current query
        prompt_parts.append(f"User Question: {query}\n\n")
        prompt_parts.append("Please provide a detailed answer based on the SOP information above. ")
        prompt_parts.append("If the SOPs don't contain relevant information, use your general maintenance knowledge ")
        prompt_parts.append("but clearly indicate when you're going beyond the provided SOPs.")
        
        return "".join(prompt_parts)
    
    def predict_issue(self, symptoms: Dict[str, any]) -> Dict[str, any]:
        """
        Predict potential issues based on equipment symptoms
        """
        
        # Format symptoms for analysis
        symptoms_text = "\n".join([f"- {key}: {value}" for key, value in symptoms.items()])
        
        prompt = f"""{self.system_context}

Equipment Symptoms Detected:
{symptoms_text}

Based on these symptoms, provide:
1. Most likely fault/issue (with confidence level)
2. Potential root causes (ranked by probability)
3. Recommended immediate actions
4. Required spare parts or tools
5. Estimated time to resolve
6. Safety precautions

Format your response clearly with numbered sections."""

        try:
            response = self.model.generate_content(prompt)
            
            # Parse response into structured format
            return {
                'prediction': response.text,
                'symptoms': symptoms,
                'confidence': 'medium'
            }
        
        except Exception as e:
            return {
                'error': str(e),
                'symptoms': symptoms
            }
    
    def generate_maintenance_schedule(self, equipment_type: str, usage_data: Dict = None) -> str:
        """Generate preventive maintenance schedule"""
        
        usage_info = ""
        if usage_data:
            usage_info = f"\nCurrent Usage Data:\n{usage_data}"
        
        prompt = f"""{self.system_context}

Generate a preventive maintenance schedule for: {equipment_type}
{usage_info}

Provide:
1. Daily checks
2. Weekly maintenance tasks
3. Monthly maintenance tasks
4. Quarterly inspections
5. Annual overhaul checklist

Include estimated time for each task and required personnel."""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating schedule: {str(e)}"
    
    def explain_sop_step(self, step_description: str) -> str:
        """Provide detailed explanation of a specific SOP step"""
        
        prompt = f"""{self.system_context}

Explain this maintenance procedure step in detail:
"{step_description}"

Provide:
1. Purpose of this step
2. Detailed instructions
3. Common mistakes to avoid
4. Safety considerations
5. Expected outcome"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error explaining step: {str(e)}"



