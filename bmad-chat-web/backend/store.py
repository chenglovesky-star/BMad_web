import json
import os
import uuid
from config import PROJECTS_FILE

class Store:
    def __init__(self):
        self.projects = []
        self.load()

    def load(self):
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                self.projects = json.load(f)
        else:
            self.projects = []

    def save(self):
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.projects, f, ensure_ascii=False, indent=2)

    def get_projects(self):
        return self.projects

    def get_project(self, project_id):
        for p in self.projects:
            if p['id'] == project_id:
                return p
        return None

    def create_project(self, name, path):
        project = {
            'id': str(uuid.uuid4()),
            'name': name,
            'path': path,
            'conversations': []
        }
        self.projects.append(project)
        self.save()
        return project

    def delete_project(self, project_id):
        self.projects = [p for p in self.projects if p['id'] != project_id]
        self.save()

    def add_conversation(self, project_id, conversation):
        project = self.get_project(project_id)
        if project:
            project['conversations'].append(conversation)
            self.save()

    def get_conversations(self, project_id):
        project = self.get_project(project_id)
        return project['conversations'] if project else []

store = Store()
