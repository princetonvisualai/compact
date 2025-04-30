import os, json, time
from .generator import generate_questions
from .verifier import verify_question_capabilities
import google.generativeai as genai

def process_single_image(args):
    filename, image_dir, api_key, output_file, file_lock, counter, k, print_intermediate = args
    
    # Configure Gemini API with the provided key
    genai.configure(api_key=api_key)
    
    image_path = os.path.join(image_dir, filename)
    
    try:
        result = generate_questions(genai, image_path, k=k)
        
        if result:
            # Get a unique ID for this entry using the counter
            with file_lock:
                entry_id = counter.value
                counter.value += 1
                
            entry = {
                "id": f"llava_{entry_id}",
                "image": filename,
                "conversations": []
            }
            
            # Add each Q&A pair as two conversation entries
            verified_questions = []
            verification_attempts = 0
            max_verification_attempts = 10  # Limit attempts to avoid infinite loops
            
            # Track question topics to avoid repetition
            question_topics = set()
            
            # Continue verification attempts until we get 2-3 good questions or reach max attempts
            while len(verified_questions) < 2 and verification_attempts < max_verification_attempts:
                for q in result['questions']:
                    # Skip if already verified enough questions
                    if len(verified_questions) >= 3:
                        break
                        
                    # Skip questions with uninformative answers or low confidence
                    if not q.get('answer') or q.get('answer').lower() in ['none', 'unknown', 'not visible', 'not applicable', 'n/a'] or q.get('confidence', 0) < 70:
                        continue
                    
                    # Simple check for question similarity - skip if too similar to existing questions
                    # Extract key words for comparison (nouns and main objects)
                    question_words = set(q['question'].lower().split())
                    is_too_similar = False
                    
                    for vq in verified_questions:
                        vq_words = set(vq['question'].lower().split())
                        # If questions share more than 60% of words, consider them too similar
                        common_words = question_words.intersection(vq_words)
                        similarity_ratio = len(common_words) / min(len(question_words), len(vq_words))
                        if similarity_ratio > 0.6:
                            is_too_similar = True
                            break
                            
                    if is_too_similar:
                        continue
                    
                    # Verify the question
                    verification = verify_question_capabilities(
                        genai, 
                        q['question'], 
                        q['answer'], 
                        q['capabilities'], 
                        k,
                        print_intermediate=print_intermediate
                    )
                    
                    if verification and verification['valid']:
                        verified_questions.append(q)
                        question_topics.update(question_words)
                
                # If we don't have enough verified questions, try generating more
                if len(verified_questions) < 2:
                    verification_attempts += 1
                    # Generate more questions
                    additional_result = generate_questions(genai, image_path, k=k)
                    if additional_result and 'questions' in additional_result:
                        result['questions'].extend(additional_result['questions'])
                else:
                    # We have enough verified questions
                    break
            
            # Only proceed if we have at least 2 verified questions
            if len(verified_questions) >= 2:
                # Keep only 2-3 verified questions
                verified_questions = verified_questions[:3]
                
                # Only use verified questions
                for i, q in enumerate(verified_questions):
                    cap_key = 'capabilities' if 'capabilities' in q else 'capability'
                    
                    question_text = f"<image>\n{q['question']}\nAnswer the question using a single word or phrase." if i == 0 else q['question']
                    
                    entry["conversations"].extend([
                        {
                            "from": "human",
                            "value": question_text,
                            "capability": q[cap_key]
                        },
                        {
                            "from": "gpt",
                            "value": q['answer']
                        }
                    ])
                
                with file_lock:
                    # Safely write to file
                    with open(output_file, 'a') as f:
                        json.dump([entry], f, indent=4)
                        f.write('\n')
                        f.flush()
                
                return entry
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "rate limit" in str(e).lower():
            print(f"\nRate limit hit! Waiting... Error: {str(e)}")
            time.sleep(20)  # Wait for 20 seconds before retrying
            return process_single_image(args)  # Retry the same image
        print(f"\nError processing {filename}: {str(e)}")
    return None
