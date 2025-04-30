import json, random, time
from .prompts import get_system_prompt
from .config import VALID_CAPABILITIES
from .utils import clean_json_response

def generate_questions(client, image_path, k=2):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    system_prompt = get_system_prompt(k)

    # Generate 2-3 questions with different capability pairs
    num_questions = random.randint(2, 3)
    all_questions = []
    used_capability_pairs = set()
    used_capabilities = set()  

    for _ in range(num_questions):
        available_capabilities = [c for c in VALID_CAPABILITIES if c not in used_capabilities]
        
        if len(available_capabilities) < k:
            available_capabilities = VALID_CAPABILITIES
        
        weighted_capabilities = available_capabilities.copy()
        weighted_capabilities.extend(['action_recognition'] * weighted_capabilities.count('action_recognition'))
        
        while True:
            sampled_capabilities = random.sample(weighted_capabilities, k)
            if len(set(sampled_capabilities)) == k:
                cap_tuple = tuple(sorted(sampled_capabilities))
                if cap_tuple not in used_capability_pairs:
                    used_capability_pairs.add(cap_tuple)
                    for cap in cap_tuple:
                        used_capabilities.add(cap)
                    break

        capability_prompt = f"Generate a question using EXACTLY these {k} capabilities: {' and '.join(cap_tuple)}"
        
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                model = client.GenerativeModel('models/gemini-2.0-flash')
                
                retry_prompt = f"Attempt {retry_count + 1}/{max_retries}: " if retry_count > 0 else ""
                prompt = system_prompt + "\n\n" + retry_prompt + capability_prompt
                
                response = model.generate_content(
                    contents=[
                        prompt,
                        {"mime_type": "image/jpeg", "data": image_data}
                    ],
                    generation_config={
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "max_output_tokens": 1000,
                    }
                )
                
                content = response.text.strip()
                
                if content.startswith('```'):
                    lines = content.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines[-1].startswith('```'):
                        lines = lines[:-1]
                    content = '\n'.join(lines)
                
                content = content.replace('```json', '').replace('```', '').strip()
                
                try:
                    result = json.loads(content)
                    if isinstance(result, dict) and 'questions' in result:
                        valid_questions = []
                        for q in result['questions']:
                            q['capabilities'] = list(cap_tuple)
                            # Check for uninformative answers
                            if not q.get('answer') or q.get('answer').lower() in ['none', 'unknown', 'not visible', 'not applicable', 'n/a', 'unavailable', 'n/a', 'unclear']:
                                continue
                            q['confidence'] = 90
                            valid_questions.append(q)
                        
                        if valid_questions:  # If we got valid questions, add them and break
                            all_questions.extend(valid_questions)
                            break
                        
                except json.JSONDecodeError as je:
                    print(f"JSON parsing error for {image_path} (attempt {retry_count + 1}): {str(je)}")
                
                retry_count += 1
                if retry_count < max_retries:
                    print(f"No valid questions generated, retrying ({retry_count + 1}/{max_retries})...")
                    time.sleep(1)  # Add small delay between retries
                    
            except Exception as e:
                print(f"API error processing {image_path} (attempt {retry_count + 1}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"API error, retrying ({retry_count + 1}/{max_retries})...")
                    time.sleep(1)  # Add small delay between retries
                continue
    
    return {'questions': all_questions} if all_questions else None