import json
from .prompts import get_verification_prompt
from .utils import clean_json_response

def verify_question_capabilities(client, question, answer, expected_capabilities, k, print_intermediate=False):
    system_prompt = get_verification_prompt(k)
    try:
        model = client.GenerativeModel('models/gemini-2.0-flash')
        
        user_content = f"""Question: {question}
        Answer: {answer}
        Expected capabilities: {expected_capabilities}

        Verify if this question naturally requires exactly these {k} capabilities."""
        
        response = model.generate_content(
            contents=[system_prompt, user_content],
            generation_config={
                "temperature": 0.1,
                "top_p": 0.9,
                "max_output_tokens": 500,
            }
        )
        
        content = response.text.strip()
        if content.startswith('```'):
            content = content.split('```')[1].strip()
            if content.startswith('json'):
                content = content[4:].strip()
        
        result = json.loads(content)
        
        # Add debug logging only if print_intermediate is True
        if print_intermediate:
            actual_capabilities = len(result.get('capabilities_used', []))
            print(f"\nVerification Results:")
            print(f"Question: {question}")
            print(f"Expected capabilities ({k}): {expected_capabilities}")
            print(f"Actual capabilities ({actual_capabilities}): {result.get('capabilities_used', [])}")
            print(f"Valid: {result.get('valid', False)}")
            print(f"Reason: {result.get('reason', 'No reason provided')}")
            print("-" * 80)
        
        # Check if the number of capabilities matches k
        if len(result.get('capabilities_used', [])) != k:
            if print_intermediate:
                print(f"Rejecting question: Number of capabilities ({len(result.get('capabilities_used', []))}) doesn't match k={k}")
            result['valid'] = False
        
        return result
        
    except Exception as e:
        if print_intermediate:
            print(f"Verification error: {str(e)}")
        return None