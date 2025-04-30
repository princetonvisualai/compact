def get_system_prompt(k):
    return f"""You are an AI assistant that generates challenging but well-defined questions and answers about images. 
    First, I will provide you with {k} specific capabilities. Generate 1 question that naturally integrates EXACTLY these {k} capabilities.
    
    IMPORTANT: 
    - If the question can be answered without looking at the image (e.g., the answer can be inferred from the question itself or previous questions), it's a BAD question
    - Questions should be reasonably challenging but must have clear, unambiguous answers
    - All answers must be extremely concise - use only a single word or short phrase
    - Each question must be a single, integrated question that naturally combines all {k} given capabilities
    - DO NOT use "and" or commas to combine separate questions
    - Questions should require careful observation and reasoning
    - Only generate questions when you can determine the answer with high confidence
    - Avoid subjective or ambiguous questions
    - ONLY ask about objects and capabilities that are ACTUALLY PRESENT in the image
    - NEVER create questions about objects or features that don't exist in the image
    - Generate diverse questions that differ in topic and required reasoning
    
    CAPABILITY DEFINITIONS:
    - spatial_relationship: Identifying how specific objects are positioned relative to each other (above, below, next to, inside, etc.) - focuses on the direct relationship between two or more particular objects
    - spatial_recognition: Understanding the overall spatial layout and arrangement of the entire scene - focuses on the general organization, depth, perspective, or environmental context, rather than relationships between specific objects
    - text_recognition: Reading and interpreting text visible in the image 
    - action_recognition: Identifying what action is being performed (can involve a single person/object)
    - object_interaction: Analyzing how multiple objects interact with each other (requires at least two objects) - MUST involve at least one moving/active object, not just static objects positioned together - can include humans interacting with objects and humans interacting with humans
    - object_recognition: Identifying and naming objects present in the image
    - counting: Determining the number of instances of something in the image
    - color: Identifying or comparing colors of objects in the image
    - shape: Recognizing and describing the shapes of objects in the image
    - scene_understanding: Identifying where the image is taken or the type of environment/setting (indoor/outdoor, beach, mountain, kitchen, office, etc.) - focuses on identifying the overall scene, background, or context of the image
    
    Examples:
    - BAD: "What color is the car, and where is it located?" (two separate questions)
    - BAD: "What might the person be thinking?" (subjective/ambiguous)
    - BAD: "Is this a nice room?" (subjective)
    - BAD: "What breed of dog is in the corner?" (when no dog exists in the image)
    - BAD: "How are the fridge and desk interacting?" (static objects don't qualify as interaction)
    - BAD: "What is the color of the red car?" (answer can be inferred from the question itself without seeing the image)
    - GOOD: "What color car is parked next to the red brick building?" (specific, clear answer)
    - GOOD: "How many yellow tennis balls are visible on the wooden court?" (requires counting + color)
    - GOOD: "What is the person in blue using to interact with the television?" (proper object interaction)
    - GOOD: "Where is this image taken?" (scene understanding)
    - GOOD: "Where is this scene happening?" (scene understanding)
    
    Format your response as a JSON object with fields:
    {{
        "questions": [
            {{
                "question": "...",
                "answer": "...",  # Must be a single word or short phrase
                "capabilities": ["capability1", "capability2", ...]  # These must match the provided capabilities
            }}
        ]
    }}
    
    IMPORTANT: Return ONLY valid JSON without any markdown formatting."""


def get_verification_prompt(k):
    return f"""You are an AI assistant that verifies if questions about images properly utilize specified capabilities.
    
    Given a question and its answer, analyze whether it NATURALLY requires using EXACTLY {k} specified capabilities - no more, no less.
    
    IMPORTANT:
    - The question should require ALL specified capabilities to be answered
    - The question should not require additional major capabilities beyond those specified
    - The capabilities must be naturally integrated, not artificially forced
    
    Return your response as a JSON object with fields:
    {{
        "valid": true/false,
        "reason": "Brief explanation of why the question is valid or invalid",
        "capabilities_used": ["list", "of", "actually", "used", "capabilities"]
    }}"""