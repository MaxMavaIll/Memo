import json

class WorkWithJson():
    def __init__(self, file: str) -> None:
        self.file = file
        
    def get_json(self) -> dict:
        with open(self.file) as file:
            data = json.load(file)

        return data
    
    def set_json(self, data: dict = {}) -> None:
        with open(self.file, 'w') as file:
            json.dump(data, file)