# Taskmaster-
An ultimate task management systems  

# Overview  
This document serves as comprehensive documentation for the project Taskmaster, a platform built with Django REST Framework for the backend, HTML, jQuery, Ajax, and Tailwind CSS for the frontend. This platform allows users to manage projects and tasks by providing functionalities such as adding, deleting, and updating tasks.  


## Table of Contents  

- Installation  
- Frontend Implementation
- Backend Setup
- API Endpoints
- Navigation around the page
- Testing
# installation  
To set up the project locally, follow these steps:  

1. Clone the repository from [GitHub Repo URL].
2. Install the required backend dependencies using `pip install -r requirements.txt`.
3. Configure the database settings in `settings.py`.
4. Run migrations using `python manage.py migrate`.
5. Start the development server with `python manage.py runserver`.
6. install the needed frontend node_modules by running npm install.
7. make sure the package.json files are present.

# Frontend setup  
once npm install is successful, you can run your html through any means possible  
# Backend setup
once `python manage.py runserver` is running successfully, you are good to go.  
**API Endpoints**  
The following API endpoints are available for managing tasks:  
    - POST /tasks/create/: Create a new task.
    - GET /tasks/list/: List all tasks.
    - DELETE /tasks/delete/<name>/: Delete a task by name.
    - PUT /tasks/update/<pk>/: Update a task by primary key.    
    
| Endpoint                   | Method | Description                       |Requirements|
|----------------------------|--------|-----------------------------------|------------|
| `/tasks/create/`          | POST   | Create a new task.               |name, contributors, expires, image|
| `/tasks/list/`            | GET    | List all tasks.                  |
| `/tasks/delete/<name>/`   | DELETE | Delete a task by name.           |
| `/tasks/update/<name>/`   | PATCH    | Update a task by primary key.  |name, contributors, expires, image|  
| `/finish-tasks/<name>/`   | POST   | Sets a task to completed.      |
| `/search/`                | GET    | Searches the database based on any keywords/fields.|

**Navigation around the page**  
    - From top to bottom, the search bar is for searching, the add icon at th extreme end is for adding tasks.  
    - The `All` box is for filtering between different status of the task.  
    - The back arrow before `17 found` is for navigating back from the search and filtered tasks to the whole tasks  
    - The three dots that looks like semicolon is used for editing. There you can delete, update or finish a task.


  
