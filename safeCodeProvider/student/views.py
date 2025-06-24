import csv  
import os  
import json
import subprocess  
from django.shortcuts import render 
from django.http import JsonResponse  
from django.conf import settings

UPLOADS_DIR = "uploads"

def student_control(request):
    if request.method == 'POST':  
        student_id = request.POST.get('student_id')
        student_name = request.POST.get('student_name') 
        exam_password = request.POST.get('exam_password') 

        config_path = os.path.join(settings.BASE_DIR, 'config.json') 
        try:
            with open(config_path, 'r') as config_file:  
                config_data = json.load(config_file)  
                correct_password = config_data.get('exam_password')  
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Exam configuration not found'})  

        if exam_password != correct_password:  
            return JsonResponse({'status': 'error', 'message': 'Invalid exam password. Please try again.'})

        student_list_path = os.path.join(settings.MEDIA_ROOT, 'student_list')  
        try:
            files = os.listdir(student_list_path)
            if files:
                student_list_file = os.path.join(student_list_path, files[0])
            else:
                return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  
 
        try:
            with open(student_list_file, 'r', encoding='utf-8') as csvfile:  
                reader = csv.reader(csvfile)  
                student_exists = any(
                    row[0] == student_id and row[1].lower() == student_name.lower() 
                    for row in reader
                )
        except FileNotFoundError:
            return JsonResponse({'status': 'error', 'message': 'Student list file not found'})  

        if not student_exists:  
            return JsonResponse({'status': 'error', 'message': 'Student not found in the list'})  

# Determine the full path of the JSON file
        json_path = os.path.join(settings.BASE_DIR, "students.json")

        # Read the JSON file
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as json_file:
                students_data = json.load(json_file)  # Get JSON data as a list
        
        # Check the user's ID and update the isLogged value
            user_found = False
            for student in students_data:
                if student["id"] == student_id:
                    if student["isLogged"] == "true":
                        return JsonResponse({
                            "status": "error",
                            "message": "You are already logged in and cannot enter the exam."
                        })
                    student["isLogged"] = "true"
                    user_found = True
                    break

            if user_found:
                # Write the updated data back to the JSON file
                with open(json_path, "w", encoding="utf-8") as json_file:
                    json.dump(students_data, json_file, indent=4, ensure_ascii=False)


            else:
                return JsonResponse({"status": "error", "message": "Student ID not found"})
            
        return JsonResponse({
        'status': 'success',
        'redirect_url': '/exam/',
        'student_id': student_id,
        'student_name': student_name
    })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})  

def student_login(request):  
    return render(request, 'student_login.html')

def exam_page(request):
    config_path = os.path.join(settings.BASE_DIR, 'config.json')
    try:
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            exam_time = int(config_data.get('exam_time', 10))  # In minutes
            exam_type = config_data.get('exam_type', 'py')  # For example "py", "java", "c"
    except FileNotFoundError:
        exam_time = 10
        exam_type = 'py'
    
    # Dynamically find the PDF file from the exam_instruction folder (we do not hardcode the file name)
    pdf_url = ''
    exam_instruction_folder = os.path.join(settings.MEDIA_ROOT, 'exam_instruction')
    if os.path.exists(exam_instruction_folder):
        pdf_files = [f for f in os.listdir(exam_instruction_folder) if f.lower().endswith('.pdf')]
        if pdf_files:
            pdf_url = settings.MEDIA_URL + 'exam_instruction/' + pdf_files[0]
    
    # Dynamically read the file content from the assignment_file folder
    assignment_content = ''
    assignment_folder = os.path.join(settings.MEDIA_ROOT, 'assignment_file') 
    if os.path.exists(assignment_folder):
        assignment_files = [f for f in os.listdir(assignment_folder) if not f.startswith('.')]
        if assignment_files:
            file_path = os.path.join(assignment_folder, assignment_files[0])
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    assignment_content = f.read()
            except Exception as e:
                assignment_content = f"An error occurred while reading the file: {e}"
    
    return render(request, 'exam_page.html', {
        'exam_time': exam_time,
        'exam_type': exam_type,
        'pdf_url': pdf_url,
        'assignment_content': assignment_content,
    })

def save_code(request):
    try:
        body = json.loads(request.body)
        student_id = body.get('student_id')
        student_name = body.get('student_name').lower()
        files = body.get('files', {})

        folder_name = f"{student_id}_{student_name}"
        student_folder = os.path.join(UPLOADS_DIR, folder_name)

        if not os.path.exists(student_folder):
            return JsonResponse({'status': 'error', 'message': 'Student folder not found'})

        for file_name, code in files.items():
            file_path = os.path.join(student_folder, file_name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

        return JsonResponse({'status': 'success', 'message': 'All files saved'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def run_code(request):
    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        student_name = data.get("student_name")

        if not student_id or not student_name:
            return JsonResponse({"status": "error", "message": "Incomplete information was sent."})

        student_name = student_name.strip().lower()
        container_name = f"{student_id}-{student_name}-container"
        image_name = f"{student_id}-{student_name}"

        # config.json'dan exam türü ve dosya adı alınır
        config_path = "config.json"
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        base_file_name = config.get("file_name", "script").strip()
        exam_type = config.get("type", "py").strip().lower()
        file_name = f"{base_file_name}.{exam_type}"

        folder_name = f"{student_id}_{student_name}"
        student_folder = os.path.abspath(os.path.join(UPLOADS_DIR, folder_name))

        if not os.path.isdir(student_folder):
            return JsonResponse({"status": "error", "message": "Student folder not found."})

        code_file_path = os.path.join(student_folder, file_name)

        if not os.path.isfile(code_file_path):
            return JsonResponse({"status": "error", "message": f"{file_name} not found in student folder."})

        # Docker içine dosyayı kopyala
        #copy_command = f"docker cp {code_file_path} {container_name}:/app/{file_name}"
        copy_command = f"docker cp {student_folder}/. {container_name}:/app/"

        os.system(copy_command)

        # Exam türüne göre çalıştırma komutu oluştur
        docker_exec_command = ""
        if exam_type == "py":
            docker_exec_command = f"docker exec {container_name} python /app/{file_name}"
        elif exam_type == "java":
            docker_exec_command = f"docker exec {container_name} javac /app/{file_name} && docker exec {container_name} java -cp /app {base_file_name}"
        elif exam_type == "c":
            docker_exec_command = f"docker exec {container_name} gcc /app/{file_name} -o /app/{base_file_name} && docker exec {container_name} /app/{base_file_name}"
        else:
            return JsonResponse({"status": "error", "message": f"Unsupported exam type: {exam_type}"})

        # Docker komutunu çalıştır
        result = subprocess.run(
            docker_exec_command,
            shell=True,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return JsonResponse({"status": "success", "output": result.stdout})
        else:
            return JsonResponse({"status": "error", "output": result.stderr})

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON format."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Unexpected error: {str(e)}"})


def delete_docker(request):
    try:
        # Get the JSON data
        body = json.loads(request.body)

        # Get the JSON data
        student_id = body.get('student_id')
        student_name = body.get('student_name').lower()

        # Create Docker container and image names
        container_name = f"{student_id}-{student_name}-container"
        image_name = f"{student_id}-{student_name}"

        # First, stop and remove the container
        stop_container_command = f"docker stop {container_name} && docker rm {container_name}"
        delete_image_command = f"docker rmi -f {image_name}"

        print(f"Stopping and removing container: {container_name}")
        os.system(stop_container_command)  # Stop and remove the container
        print(f"Removing image: {image_name}")
        os.system(delete_image_command)  # Delete the image

        return JsonResponse({'status': 'success', 'message': 'Docker container and image deleted successfully!'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def list_assignment_files(request):
    assignment_dir = os.path.join(settings.BASE_DIR, 'media', 'assignment_files')

    if not os.path.exists(assignment_dir):
        return JsonResponse({'files': []})

    files = [f for f in os.listdir(assignment_dir) if os.path.isfile(os.path.join(assignment_dir, f))]
    return JsonResponse({'files': files})