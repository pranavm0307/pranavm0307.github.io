# ai.py - Dynamic AI module for Flask chatbot

import re
import random
import datetime
from typing import Dict, List, Any

class DynamicAI:
    def __init__(self):
        self.conversation_history = []
        self.user_profiles = {}
        
        # Knowledge domains and patterns
        self.patterns = {
            'programming': ['python', 'javascript', 'programming', 'code', 'coding', 'development', 'bug', 'debug', 'algorithm'],
            'learning': ['learn', 'how to', 'tutorial', 'guide', 'teach me', 'explain', 'understand'],
            'food': ['cook', 'recipe', 'food', 'dinner', 'breakfast', 'lunch', 'meal', 'eat'],
            'career': ['job', 'career', 'resume', 'interview', 'work', 'professional', 'salary'],
            'science': ['explain', 'what is', 'how does', 'quantum', 'ai', 'machine learning', 'blockchain'],
            'creative': ['write', 'story', 'poem', 'creative', 'design', 'create', 'art'],
            'health': ['health', 'fitness', 'exercise', 'workout', 'diet', 'medical'],
            'travel': ['travel', 'trip', 'vacation', 'visit', 'destination', 'flight'],
            'math': ['calculate', 'math', 'solve', '+', '-', '*', '/', 'equation', 'number'],
            'problem': ['problem', 'issue', 'help', 'fix', 'solution', 'advice', 'trouble'],
            'personal': ['who are you', 'what are you', 'about you', 'your name'],
            'greetings': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
            'thanks': ['thank you', 'thanks', 'appreciate', 'grateful']
        }
    
    def analyze_input(self, message: str, user_id: str) -> Dict[str, Any]:
        """Analyze user input and determine context"""
        lower_message = message.lower()
        
        # Determine primary category
        category = self._categorize_message(lower_message)
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(lower_message)
        
        # Assess complexity
        complexity = self._assess_complexity(message)
        
        # Check for specific entities
        entities = self._extract_entities(lower_message)
        
        return {
            'category': category,
            'sentiment': sentiment,
            'complexity': complexity,
            'entities': entities,
            'message': message,
            'user_id': user_id
        }
    
    def generate_response(self, analysis: Dict[str, Any], message: str, user_id: str) -> Dict[str, Any]:
        """Generate contextual response based on analysis"""
        category = analysis['category']
        
        # Generate response based on category
        if category == 'programming':
            response = self._generate_programming_response(message, analysis)
        elif category == 'learning':
            response = self._generate_learning_response(message, analysis)
        elif category == 'food':
            response = self._generate_food_response(message, analysis)
        elif category == 'career':
            response = self._generate_career_response(message, analysis)
        elif category == 'science':
            response = self._generate_science_response(message, analysis)
        elif category == 'creative':
            response = self._generate_creative_response(message, analysis)
        elif category == 'health':
            response = self._generate_health_response(message, analysis)
        elif category == 'travel':
            response = self._generate_travel_response(message, analysis)
        elif category == 'math':
            response = self._generate_math_response(message, analysis)
        elif category == 'problem':
            response = self._generate_problem_response(message, analysis)
        elif category == 'personal':
            response = self._generate_personal_response(message, analysis)
        elif category == 'greetings':
            response = self._generate_greeting_response(message, analysis)
        elif category == 'thanks':
            response = self._generate_thanks_response(message, analysis)
        else:
            response = self._generate_contextual_response(message, analysis)
        
        # Calculate confidence
        confidence = self._calculate_confidence(analysis, category)
        
        return {
            'text': response,
            'confidence': confidence,
            'intent': category,
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def _categorize_message(self, message: str) -> str:
        """Determine the primary category of the message"""
        scores = {}
        
        for category, keywords in self.patterns.items():
            score = sum(1 for keyword in keywords if keyword in message)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def _analyze_sentiment(self, message: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'like', 'happy', 'excited']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'sad', 'frustrated', 'angry', 'confused']
        
        pos_count = sum(1 for word in positive_words if word in message)
        neg_count = sum(1 for word in negative_words if word in message)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        return 'neutral'
    
    def _assess_complexity(self, message: str) -> str:
        """Assess message complexity"""
        if len(message) > 100 or message.count('?') > 1:
            return 'high'
        elif len(message) > 50 or any(word in message.lower() for word in ['how', 'why', 'explain', 'complex']):
            return 'medium'
        return 'low'
    
    def _extract_entities(self, message: str) -> List[str]:
        """Extract key entities from message"""
        tech_entities = ['python', 'javascript', 'react', 'ai', 'machine learning', 'data science']
        return [entity for entity in tech_entities if entity in message]
    
    def _calculate_confidence(self, analysis: Dict[str, Any], category: str) -> float:
        """Calculate confidence score"""
        base_confidence = 0.7
        
        # Increase confidence for specific categories we handle well
        if category in ['programming', 'learning', 'science']:
            base_confidence += 0.2
        
        # Adjust based on complexity
        if analysis['complexity'] == 'low':
            base_confidence += 0.1
        elif analysis['complexity'] == 'high':
            base_confidence -= 0.1
        
        return min(max(base_confidence, 0.1), 0.95)
    
    # Response generators for each category
    def _generate_programming_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate programming-specific responses"""
        lower_message = message.lower()
        
        if 'python' in lower_message:
            if 'learn' in lower_message:
                return """Great choice! Here's how to learn Python effectively:

**Start with basics:**
• Install Python from python.org
• Learn syntax: variables, loops, functions
• Practice with online platforms like Codecademy

**Build projects:**
• Calculator app
• To-do list
• Web scraper
• Simple game

**Next steps:**
• Choose specialization (web dev, data science, automation)
• Learn frameworks like Django/Flask
• Join Python communities

Would you like specific guidance on any area?"""
            else:
                return """Python is excellent for:
• **Beginner-friendly:** Clear, readable syntax
• **Versatile:** Web development, data science, AI
• **Strong ecosystem:** Huge library collection
• **High demand:** Great career opportunities

What specific aspect of Python interests you?"""
        
        elif 'javascript' in lower_message:
            return """JavaScript is the language of the web! Here's what makes it powerful:

**Core strengths:**
• Runs everywhere: browsers, servers, mobile apps
• Dynamic and flexible
• Huge job market

**Learning path:**
1. Basics: Variables, functions, DOM
2. Modern JS: ES6+, async/await
3. Frameworks: React, Vue, or Angular
4. Backend: Node.js

**Project ideas:**
• Interactive website
• Weather app with API
• Todo list app

Want me to elaborate on any specific part?"""
        
        else:
            return """Programming is a fantastic skill! Here's my advice:

**Choose based on goals:**
• **Web development:** JavaScript + HTML/CSS
• **Data science:** Python or R
• **Mobile apps:** Swift (iOS) or Kotlin (Android)

**Learning strategy:**
1. Pick ONE language initially
2. Learn fundamentals: variables, loops, functions
3. Build small projects immediately
4. Join coding communities

What type of programming interests you most?"""
    
    def _generate_learning_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate learning-focused responses"""
        return """Great question about learning! Here's my effective approach:

**The SMART Learning Method:**
• **S**pecific goals
• **M**easurable progress
• **A**ctive practice
• **R**elevant to your goals
• **T**ime-bound milestones

**Universal principles:**
1. **Start small:** 15-20 minutes daily
2. **Practice retrieval:** Test yourself regularly
3. **Teach others:** Explain concepts
4. **Stay consistent:** Build habits

**For any skill:**
• Find quality resources
• Join learning communities
• Apply knowledge immediately
• Embrace mistakes as learning opportunities

What specifically would you like to learn?"""
    
    def _generate_food_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate food/cooking responses"""
        lower_message = message.lower()
        
        if 'dinner' in lower_message or 'tonight' in lower_message:
            return """Here are delicious dinner ideas:

**Quick & Easy (30 mins):**
• Stir-fry with vegetables + rice
• Pasta with garlic and olive oil
• Chicken with roasted vegetables
• Tacos with beans and fresh toppings

**Comfort Food:**
• Grilled cheese and tomato soup
• Spaghetti and meatballs
• Chicken fried rice

**Healthy Options:**
• Salmon with quinoa and broccoli
• Mediterranean bowl with hummus
• Lentil curry with brown rice

What type of cuisine do you prefer?"""
        
        elif 'recipe' in lower_message:
            return """Here's a versatile stir-fry recipe:

**Simple Stir-Fry (serves 2-3):**
• 2 cups mixed vegetables
• 1 protein (chicken/tofu/shrimp)
• 2 tbsp oil
• 2 cloves garlic, minced
• 2 tbsp soy sauce
• 1 tsp honey

**Instructions:**
1. Heat oil in large pan
2. Add protein, cook until done
3. Add vegetables (hard ones first)
4. Add garlic, stir 30 seconds
5. Mix soy sauce and honey, add to pan
6. Serve over rice

**Tips:** Swap vegetables based on what you have!

What type of recipe are you looking for?"""
        
        else:
            return """Food is such a joy! Here are cooking tips:

**Kitchen essentials:**
• Sharp knife and cutting board
• Good non-stick pan
• Basic spices: salt, pepper, garlic, paprika

**Cooking principles:**
• Taste as you go
• Don't overcrowd the pan
• Prep ingredients first

**Meal planning:**
• Plan 3-4 meals, repeat favorites
• Prep on weekends
• Keep backup easy meals

What specific cooking help do you need?"""
    
    def _generate_career_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate career-focused responses"""
        lower_message = message.lower()
        
        if 'resume' in lower_message:
            return """Here's how to create a standout resume:

**Structure (1-2 pages):**
1. **Header:** Name, phone, email, LinkedIn
2. **Summary:** 2-3 lines highlighting value
3. **Experience:** Focus on achievements
4. **Skills:** Relevant technical and soft skills
5. **Education:** Degree, school, year

**Writing tips:**
• Use action verbs (achieved, developed, led)
• Quantify results ("increased sales by 20%")
• Tailor to each job
• Use keywords from job description

**Avoid:**
• Generic objectives
• Listing duties vs achievements
• Typos and errors

Need help with a specific section?"""
        
        elif 'interview' in lower_message:
            return """Interview success comes from preparation!

**Before the interview:**
• Research the company thoroughly
• Review job description
• Prepare STAR method examples
• Practice common questions
• Prepare questions to ask them

**STAR Method:**
• **Situation:** Set context
• **Task:** Your responsibility
• **Action:** What you did
• **Result:** The outcome

**Common questions:**
• "Tell me about yourself"
• "Why this role?"
• "Describe a challenge you overcame"

**Day of interview:**
• Arrive 10-15 minutes early
• Bring extra resumes
• Maintain eye contact
• Follow up within 24 hours

What type of interview are you preparing for?"""
        
        else:
            return """Career development is a journey! Strategic advice:

**Planning steps:**
1. **Self-assessment:** Strengths, interests, values
2. **Goal setting:** Short and long-term goals
3. **Skill development:** Identify gaps
4. **Networking:** Build relationships
5. **Experience:** Gain relevant experience

**Growth strategies:**
• Seek feedback regularly
• Take stretch assignments
• Find a mentor
• Keep learning new skills

**Job search tips:**
• Use multiple channels
• Customize applications
• Follow up appropriately

What career aspect would you like to focus on?"""
    
    def _generate_science_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate science/tech explanations"""
        lower_message = message.lower()
        
        if 'quantum' in lower_message:
            return """Quantum computing explained simply:

**Classical vs Quantum:**
• **Classical:** bits are 0 or 1 (like switches)
• **Quantum:** qubits can be 0, 1, or both!

**Key concepts:**
• **Superposition:** Multiple states simultaneously
• **Entanglement:** Connected qubits affect each other
• **Interference:** Amplify correct answers

**Why it matters:**
• **Speed:** Exponentially faster for certain problems
• **Applications:** Drug discovery, cryptography, AI

**Current state:**
• Still experimental and expensive
• Companies like IBM, Google leading development

**Simple analogy:**
Classical computing checks every book in a library one by one. Quantum computing checks all books simultaneously!

What aspect interests you most?"""
        
        elif 'ai' in lower_message:
            return """AI explained clearly:

**What is AI?**
Computer systems performing tasks requiring human intelligence - recognizing images, understanding speech, making decisions.

**Types:**
• **Narrow AI:** Specific tasks (Siri, recommendations)
• **General AI:** Human-level (doesn't exist yet)

**How AI learns:**
• **Machine Learning:** Find patterns in data
• **Deep Learning:** Neural networks like brain
• **Training:** Feed lots of examples

**Applications:**
• Healthcare: Disease diagnosis
• Transportation: Self-driving cars
• Business: Fraud detection
• Entertainment: Content recommendations

**Limitations:**
• Needs lots of data
• Can be biased
• Doesn't truly "understand"

What AI application interests you?"""
        
        else:
            return """I'd love to explain that concept! Could you specify what you'd like me to explain?

I excel at breaking down:
• Technology concepts (AI, blockchain, programming)
• Science topics (physics, chemistry, biology)
• Complex systems and processes

I use simple analogies and examples to make difficult concepts understandable.

What would you like to understand better?"""
    
    def _generate_creative_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate creative project responses"""
        return """Creative projects are so rewarding! Here's my approach:

**The creative process:**
1. **Inspiration:** Gather ideas everywhere
2. **Brainstorming:** Generate without judgment
3. **Selection:** Choose promising concepts
4. **Development:** Expand your idea
5. **Creation:** Bring vision to life
6. **Refinement:** Polish your work

**Overcoming blocks:**
• Change environment
• Try different approaches
• Set small goals
• Take breaks
• Get fresh perspectives

**Building habits:**
• Regular creative time
• Keep idea journal
• Experiment freely
• Study admired work
• Share for feedback

What type of creative project interests you?"""
    
    def _generate_health_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate health/wellness responses"""
        return """I appreciate your health question! Remember to consult healthcare providers for personalized advice.

**General wellness principles:**
• **Nutrition:** Variety of whole foods, stay hydrated
• **Exercise:** 150 minutes moderate activity weekly
• **Sleep:** 7-9 hours quality sleep
• **Stress:** Relaxation techniques, social connections

**For fitness goals:**
• Start slowly, increase gradually
• Include cardio and strength training
• Find enjoyable activities
• Listen to your body

**Mental health matters:**
• Practice mindfulness
• Maintain social connections
• Seek professional help when needed

**See healthcare providers for:**
• New symptoms
• Health changes
• Personalized advice

What wellness aspect interests you?"""
    
    def _generate_travel_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate travel-related responses"""
        return """Travel planning made easier!

**Pre-trip planning:**
• **Budget:** Include all costs plus emergency funds
• **Research:** Local customs, currency, attractions
• **Book early:** Better prices for flights and hotels
• **Documents:** Copies of important papers

**Packing essentials:**
• Check weather forecast
• Pack light but include destination essentials
• Don't forget chargers and adapters

**During your trip:**
• Stay flexible for spontaneous experiences
• Try local food and meet locals
• Keep emergency contacts handy
• Document journey but live in the moment

**Safety tips:**
• Notify banks of travel plans
• Research common local scams
• Get travel insurance
• Trust your instincts

Where are you thinking of traveling?"""
    
    def _generate_math_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate math help responses"""
        # Try to solve simple math if present
        numbers = re.findall(r'\d+', message)
        if len(numbers) >= 2 and any(op in message for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divided']):
            return f"""I can help with math calculations and concepts!

**For this calculation:** I see numbers {', '.join(numbers)} in your message.

**Math help I provide:**
• **Calculations:** Basic arithmetic to complex equations
• **Explanations:** Step-by-step problem solving
• **Concepts:** Mathematical principles and formulas
• **Word problems:** Breaking down complex scenarios

**Learning tips:**
• Practice regularly
• Understand the 'why' not just 'how'
• Show your work to catch errors
• Use real-world examples

**Common areas:**
• Arithmetic and fractions
• Algebra and equations
• Geometry and measurements
• Statistics and probability

What specific math help do you need?"""
        
        return """I'd be happy to help with math!

**Types of help:**
• Calculations and equations
• Concept explanations
• Problem-solving strategies
• Study techniques

**My approach:**
1. Understand the problem
2. Choose the right method
3. Work step-by-step
4. Check the answer

What specific math topic or problem can I help with?"""
    
    def _generate_problem_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate problem-solving responses"""
        return """I'm here to help solve this systematically!

**Problem-solving framework:**
1. **Define clearly:** What exactly is the issue?
2. **Gather info:** What do you know vs need to know?
3. **Generate solutions:** Brainstorm multiple options
4. **Evaluate options:** Pros, cons, resources needed
5. **Choose and implement:** Select best solution
6. **Monitor:** Track progress and adjust

**Techniques:**
• **5 Whys:** Keep asking why to find root causes
• **Pros/cons lists:** Systematic evaluation
• **Outside perspectives:** Get fresh insights
• **Small tests:** Try solutions on small scale

**Consider:**
• Short-term fixes vs long-term solutions
• Available resources and constraints
• Potential risks and benefits

Could you share more details about your specific problem? I can provide more targeted guidance."""
    
    def _generate_personal_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate responses about the AI itself"""
        responses = [
            """I'm an AI assistant designed to provide helpful, contextual responses! Unlike basic chatbots, I:

**Analyze your questions** to understand intent and context
**Provide specific answers** rather than generic responses  
**Adapt my style** to match what you need
**Remember our conversation** and build on topics
**Focus on being genuinely useful** not just conversational

**My strengths:**
• Explaining complex topics simply
• Step-by-step guidance and problem-solving
• Learning and skill development support
• Adapting to different question types

I aim to give you the kind of response a knowledgeable friend would - specific, helpful, and tailored to your actual question.

What would you like to know or discuss?""",
            
            """I'm a dynamic AI built for meaningful conversations! My goal is understanding what you really need and providing genuinely useful responses.

**How I work:**
• Analyze context and intent behind questions
• Draw from broad knowledge for specific answers
• Adapt based on conversation type
• Anticipate follow-up questions

**What I enjoy helping with:**
• Detailed, specific information and explanations
• Breaking down complex topics
• Learning new skills and solving problems
• Thoughtful discussions on your interests

Think of me as a knowledgeable colleague ready to help with whatever you're working on or curious about.

How can I help you today?"""
        ]
        return random.choice(responses)
    
    def _generate_greeting_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate greeting responses"""
        greetings = [
            "Hello! How can I assist you today? 😊",
            "Hi there! What would you like to know?",
            "Hey! I'm here to help. What's on your mind?",
            "Good day! How may I be of service?",
            "Hi! Ready to help with whatever you need!"
        ]
        return random.choice(greetings)
    
    def _generate_thanks_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate thank you responses"""
        thanks_responses = [
            "You're very welcome! Happy to help! 😊",
            "My pleasure! Is there anything else you'd like to know?",
            "Glad I could help! Feel free to ask more questions.",
            "You're welcome! I'm here whenever you need assistance.",
            "Anytime! That's what I'm here for!"
        ]
        return random.choice(thanks_responses)
    
    def _generate_contextual_response(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate contextual responses for unmatched queries"""
        responses = [
            f"""I understand you're asking about this topic. To give you the most helpful response, could you provide more context about what specifically you'd like to know?

I can offer:
• Detailed explanations with examples
• Step-by-step guidance  
• Practical advice and applications
• Comparisons between different approaches

What aspect interests you most?""",
            
            f"""That's an interesting question! I'd love to help you explore this further. 

Depending on what you're looking for, I can provide:
• Comprehensive explanations
• Real-world examples
• Different perspectives and approaches
• Practical implementation guidance

What specific information would be most useful to you?""",
            
            f"""I can definitely help with that! To give you the most valuable response, it would be helpful to know more about your specific situation.

Are you looking for:
• General information and overview
• Specific instructions or how-to guidance  
• Troubleshooting help
• Comparative analysis
• Something else entirely?

Please share more details about what you need!"""
        ]
        return random.choice(responses)


# Initialize the AI instance
ai_instance = DynamicAI()

# Main functions for Flask app
def analyze_input(message: str, user_id: str) -> Dict[str, Any]:
    """Main function called by Flask app"""
    return ai_instance.analyze_input(message, user_id)

def generate_response(analysis: Dict[str, Any], message: str, user_id: str) -> Dict[str, Any]:
    """Main function called by Flask app"""
    return ai_instance.generate_response(analysis, message, user_id)