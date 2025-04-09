import json

def extract_messages(json_file, target_speaker, output_file):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    messages = [entry["message"] for entry in data if entry["speaker"] == target_speaker]
    
    word_count = 0
    selected_messages = []
    
    for msg in messages:
        words = msg.split()
        if word_count + len(words) > 1000:
            break
        selected_messages.append(msg)
        word_count += len(words)
    
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n".join(selected_messages))


# Example usage
target_user = "rithin nagaraj"
extract_messages("srurin.json", target_user, "output.txt")
