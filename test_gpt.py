from collections import defaultdict
import openai
import json
import os
import subprocess
import difflib
import sys

# TODO: Include this in the grader for the other project
# TODO: Convert the problems into the JSON format
# TODO: 
#1: Extract the code from each python file
def extract_json_from_directory(abs_directory_path):
  
  # Create a list to store the JSON objects
  json_objects= {}
  # Iterate through each file in the directory
  for filename in os.listdir(abs_directory_path):
    # Get the absolute path of the file
    file_path = os.path.join(abs_directory_path, filename)
    # Check if it's a file
    if os.path.isfile(file_path):
      # Open the file and extract the JSON object
      with open(file_path, 'r') as file:
        # Read the file
        data = file.read()
        # Convert the JSON object to a Python dictionary
        json_object = json.loads(data)
        json_objects[json_object["id"]] = json_object
        # Close the file
        file.close()
        
  return json_objects



#2: Then, prompt ChatGPT to act as python executor and generate the possible errors or the correct output
def prompt_chat_gpt(problem_descriptions):
  # Create a list to store the JSON objects
  prompt_solutions = {}
  # Create a directory to store the JSON objects
  abs_directory_path = os.path.join(os.getcwd(), 'gpt_responses')
  # If the path already exists, then there is no need to reprompt ChatGPT
  if not os.path.exists(abs_directory_path):
    os.makedirs(abs_directory_path)
  # Iterate through each problem description
  for problem_id, problem_description in problem_descriptions.items():
    # Generate the prompt for ChatGPT
    chatgpt_prompt = f"The code is:\n{problem_description['code']}"
    
    # Make an API request to ChatGPT
    response = openai.ChatCompletion.create(
      model="gpt-4",  # or whatever the latest model is
      
   
       messages=[
        {"role": "system", "content": "Act as the Command-Line Interface. You do not need to excute code. Infer how the Command-Line Interface would behave. Display nothing else except the Command-Line Interface output (do not include ChatGPT thinking or planning text). Here are the specifications for acting as the Command-Line Interface: read python3 code in a text format, display raw output of the python code execution, capture both stdout and stderr in output, run incomplete or erroneous code as given, do not change or fix the given code, for the Open AI API request just return the raw output as the response, do not show any additional text from ChatGPT."},
        {"role": "user", "content": chatgpt_prompt}
    ],

      max_tokens=60,
      n=1,
      stop=None,
      temperature=0.5
    ) 
    # Save the response to a file
    filename = f"{problem_id}.json"
    # Create a directory to store the JSON objects
    full_path = os.path.join(abs_directory_path, filename)
    # Create a JSON object to store the prompt solution
    prompt_solution =  {"id": problem_id, 
        "description": problem_description['description'], 
        "output": response["choices"][0].get("message", "").get("content", ""),
        "tags": problem_description['tags'],
                              }
    # Append the prompt solution to the list
    prompt_solutions[problem_id] = prompt_solution
    # Write the prompt solution to a file
    with open(full_path, 'w') as file:
      # Convert the JSON object to a string
      json_object = json.dumps(
     prompt_solution, indent=4)
      # Write the string to the file
      file.write(json_object)
      # Close the file
      file.close()  
  return prompt_solutions

#4: Then, execute each of the python files and save the output to a file
def execute_python_code_from_directory(problem_descriptions, prompt_solutions):
  comparison_scores = {}

  for problem_id, problem_description in problem_descriptions.items():
    
    result = subprocess.run(['python3',"-c", problem_description['code']], 
                            input="Hello World",
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                       
                  text=True)
    output = result.stdout if result.stdout else result.stderr
    
    # Use SequenceMatcher to compare the two lists of lines
    comparison = difflib.SequenceMatcher(None, output, prompt_solutions[problem_id]["output"])
    ratio = comparison.real_quick_ratio()  
    comparison_scores[problem_description["id"]] = ratio
    # Prompt Chat GPT to generate the Python Interpreter output
    abs_directory_path = os.path.join(os.getcwd(), 'python_output')
    filename = f"{problem_description['id']}.txt"
    if not os.path.exists(abs_directory_path):
      os.makedirs(abs_directory_path) 
    full_path = os.path.join(abs_directory_path, filename)
    with open(full_path, 'w') as file:
        file.write(output)
        file.close()
  return comparison_scores
 
# Check if the correct number of arguments are passed (excluding the script name itself)

'''
if len(sys.argv) != 4:
    print("Usage: python script.py arg1 arg2 arg3")
    sys.exit(1)  # Exit the script with an error code

# Assign command line arguments to variables
script_name = sys.argv[0]
generate_prompt = sys.argv[1]
code_execution = sys.argv[2]
ratio_computation = sys.argv[3]
'''
# Extract the python files from the directory
problem_path = os.path.join(os.getcwd(), 'coding_problems')
problem_descriptions = extract_json_from_directory(problem_path)


### Prompt Generation Occurs Here ###

# Prompt Chat GPT to generate the Python Interpreter output
abs_directory_path = os.path.join(os.getcwd(), 'gpt_responses')
# If the path already exists, then there is no need to reprompt ChatGPT
prompt_solutions = {}
if not os.path.exists(abs_directory_path):
    os.makedirs(abs_directory_path)
    prompt_solutions = prompt_chat_gpt(problem_descriptions)
else:
    # Extract the prompt solutions from the directory
    prompt_solutions = extract_json_from_directory(abs_directory_path)


# Execute the python files and compare the output to the ChatGPT output
comparison_scores = execute_python_code_from_directory(problem_descriptions, prompt_solutions)

# Write the comparison_scores to JSON
directory = 'json_problem_scores'  # Replace with your desired path
 # Get the absolute path of the directory relative to the current working directory
json_probs_directory_path = os.path.join(os.getcwd(), directory)
if not os.path.exists(json_probs_directory_path):
  os.makedirs(json_probs_directory_path)
  
total_score = 0

tag_scores = defaultdict(int)
tag_num_problems = defaultdict(int)
for id, score in comparison_scores.items():
    directory = f"{id}"
    abs_directory_path = os.path.join(json_probs_directory_path, directory)
    if not os.path.exists(abs_directory_path):
      os.makedirs(abs_directory_path)
    # Write the code to the file
    filename = "output.json"
    output_json = {"name": f"Python Execution Output Comparison: {id}", "tags": prompt_solutions[id]["tags"], "output": score}
    for tag in prompt_solutions[id]["tags"]:
        tag_scores[tag] += score
        tag_num_problems[tag] += 1
    
    total_score += score
    full_path = os.path.join(abs_directory_path, filename)
    with open(full_path, 'w') as file:
        file.write(json.dumps(output_json, indent=4))
        file.write("\n")
        file.close()  # Close the file
print("TAG SCORES:")
print("-----------")
for tag, score in tag_scores.items():
    average_score = (score / tag_num_problems[tag]) * 100
    print(f"Tag: {tag}, score: {average_score: .2f}%")
print("-----------")
average_total_score = (total_score / len(problem_descriptions)) * 100
print(f"TOTAL SCORE, {average_total_score: .2f}%")
total_score_path = os.path.join(os.getcwd(), "")
filename = "output.json"
output_json = {"name": "Python Execution Output Comparison: Total Score", "tags": [], "output": average_total_score}
full_path = os.path.join(total_score_path, filename)
with open(full_path, 'w') as file:
    file.write(json.dumps(output_json, indent=4))
    file.write("\n")
    file.close()  # Close the file

