import os, argparse, random, time, json
from tqdm import tqdm
from multiprocessing import Manager, Pool
import google.generativeai as genai
from .processor import process_single_image

def main():
    parser = argparse.ArgumentParser(description='Generate questions from images using Gemini')
    parser.add_argument('--k', type=int, default=2)
    parser.add_argument('--num_samples', type=int, default=100)
    parser.add_argument('--image_dir', type=str, default='images')
    parser.add_argument('--output_dir', type=str, default='output')
    parser.add_argument('--api_key', type=str, required=True)
    parser.add_argument('--processes', type=int, default=4)
    parser.add_argument('--print_intermediate', action='store_true')
    args = parser.parse_args()

    genai.configure(api_key=args.api_key)
    model = genai.GenerativeModel('models/gemini-2.0-flash')
    print("API check:", model.generate_content("API connection test").text)

    os.makedirs(args.output_dir, exist_ok=True)
    output_file = os.path.join(args.output_dir, f"output_k{args.k}.json")
    with open(output_file, 'w') as f:
        f.write('')

    manager = Manager()
    file_lock = manager.Lock()
    counter = manager.Value('i', 0)

    image_files = [f for f in os.listdir(args.image_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
    random.shuffle(image_files)
    image_files = image_files[:args.num_samples]

    process_args = [(f, args.image_dir, args.api_key, output_file, file_lock, counter, args.k, args.print_intermediate) for f in image_files]

    with Pool(processes=args.processes) as pool:
        for _ in tqdm(pool.imap_unordered(process_single_image, process_args), total=len(image_files)):
            pass

if __name__ == "__main__":
    main()