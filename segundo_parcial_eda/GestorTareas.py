import heapq
import json
import os
from datetime import datetime

class TaskManager:
    def __init__(self, filename='tasks.json'):
        self.tasks = []  # Cola de prioridad de tareas
        self.completed_tasks = set()  # Conjunto de tareas completadas
        self.task_dependencies = {}  # Diccionario para rastrear dependencias inversas
        self.filename = filename
        self.counter = 0  # Contador único para las tareas
        self.load_tasks()

    def is_task_executable(self, task):
        """
        Verifica si una tarea es ejecutable basándose en sus dependencias.
        """
        if not task['dependencies']:
            return True, []
        
        pending_dependencies = [
            dep for dep in task['dependencies'] 
            if dep not in self.completed_tasks
        ]
        return len(pending_dependencies) == 0, pending_dependencies

    def add_task(self, name, priority, dependencies=None, deadline=None):
        """
        Añade una nueva tarea con dependencias flexibles y fecha de vencimiento.
        Valida que las dependencias ingresadas existan.
        """
        if not name or name.strip() == '':
            raise ValueError("El nombre de la tarea NO puede estar vacío")
        
        try:
            priority = int(priority)
        except ValueError:
            raise ValueError("La prioridad DEBE ser un número entero")
        
        dependencies = dependencies or []
        
        # Validar que las dependencias existan
        invalid_dependencies = [
            dep for dep in dependencies 
            if dep not in [task['name'] for _, _, task in self.tasks] and dep not in self.completed_tasks
        ]
        
        if invalid_dependencies:
            raise ValueError(f"Las siguientes dependencias no existen: {', '.join(invalid_dependencies)}")
        
        task = {
            'name': name,
            'priority': priority,
            'dependencies': dependencies,
            'deadline': deadline
        }
        
        self.counter += 1
        heapq.heappush(self.tasks, (priority, self.counter, task))
        
        is_executable, pending_deps = self.is_task_executable(task)
        
        for dep in dependencies:
            if dep not in self.task_dependencies:
                self.task_dependencies[dep] = []
            self.task_dependencies[dep].append(name)
        
        print(f"\n✅ Tarea '{name}' añadida exitosamente.")
        if dependencies:
            print("🔗 Dependencias requeridas:")
            for dep in dependencies:
                print(f"   - {dep}")
        if is_executable:
            print("🟢 Tarea ejecutable: Todas las dependencias están completadas.")
        else:
            print("🔴 Tarea NO ejecutable. Dependencias pendientes:")
            for dep in pending_deps:
                print(f"   - {dep}")
        
        self.save_tasks()
        return task

    def complete_task(self, task_name):
        """
        Marca una tarea como completada con reglas de dependencia.
        """
        for index, (priority, _, task) in enumerate(self.tasks):
            if task['name'] == task_name:
                # Verificar si todas las dependencias directas han sido completadas
                _, pending_dependencies = self.is_task_executable(task)
                if pending_dependencies:
                    print(f"\n❌ NO se puede completar '{task_name}'.")
                    print("Razón: Las siguientes dependencias no han sido completadas:")
                    for dep in pending_dependencies:
                        print(f"   - {dep}")
                    return

                # Verificar dependencias inversas (tareas que dependen de esta tarea)
                if task_name in self.task_dependencies:
                    dependientes = self.task_dependencies[task_name]
                    tareas_bloqueadas = [
                        dep for dep in dependientes 
                        if dep not in self.completed_tasks
                    ]
                    if tareas_bloqueadas:
                        print(f"\n❌ NO se puede completar '{task_name}'.")
                        print("Razón: Otras tareas dependen de esta:")
                        for dep in tareas_bloqueadas:
                            print(f"   - {dep}")
                        return

                # Eliminar tarea de la lista
                del self.tasks[index]
                heapq.heapify(self.tasks)

                # Marcar como completada
                self.completed_tasks.add(task_name)

                print(f"\n✅ Tarea '{task_name}' completada.")

                # Verificar ejecutabilidad de tareas restantes
                self.check_task_executability()

                # Guardar cambios
                self.save_tasks()
                return

        print(f"\n❌ Tarea '{task_name}' no encontrada.")

    def check_task_executability(self):
        """
        Verifica y notifica la ejecutabilidad de todas las tareas pendientes.
        """
        print("\n🔍 Verificando ejecutabilidad de tareas pendientes...")
        
        executable_tasks = []
        non_executable_tasks = []
        
        for priority, _, task in self.tasks:
            is_executable, pending_deps = self.is_task_executable(task)
            
            if is_executable:
                executable_tasks.append(task['name'])
            else:
                non_executable_tasks.append((task['name'], pending_deps))
        
        if executable_tasks:
            print("🟢 Tareas ejecutables:")
            for task in executable_tasks:
                print(f"   - {task}")
        
        if non_executable_tasks:
            print("🔴 Tareas NO ejecutables:")
            for task, deps in non_executable_tasks:
                print(f"   - {task}")
                print("     Dependencias pendientes:")
                for dep in deps:
                    print(f"       • {dep}")

    def load_tasks(self):
        """
        Carga las tareas desde un archivo JSON.
        """
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.tasks = [(task['priority'], index, task) for index, task in enumerate(data.get('tasks', []))]
                    self.completed_tasks = set(data.get('completed_tasks', []))
                    self.task_dependencies = data.get('task_dependencies', {})
                    self.counter = len(self.tasks)
            except (json.JSONDecodeError, FileNotFoundError):
                self.tasks = []
                self.completed_tasks = set()
                self.task_dependencies = {}
                self.save_tasks()
        else:
            self.tasks = []
            self.completed_tasks = set()
            self.task_dependencies = {}
            self.save_tasks()

    def save_tasks(self):
        """
        Guarda las tareas en un archivo JSON.
        """
        try:
            data = {
                'tasks': [task for _, _, task in self.tasks],
                'completed_tasks': list(self.completed_tasks),
                'task_dependencies': self.task_dependencies
            }
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error al guardar tareas: {e}")

def main():
    task_manager = TaskManager()

    while True:
        print("\n--- GESTOR DE TAREAS CON DEPENDENCIAS Y FECHA DE VENCIMIENTO ---")
        print("1. Añadir Tarea (con posibles dependencias y fecha de vencimiento)")
        print("2. Mostrar Tareas Pendientes")
        print("3. Completar Tarea")
        print("4. Mostrar Dependencias")
        print("5. Verificar Ejecutabilidad de Tareas")
        print("6. Salir")
        
        opcion = input("\nSelecciona una opción: ")
        
        try:
            if opcion == '1':
                nombre = input("\n📝 Nombre de la tarea: ")
                prioridad = input("🔢 Prioridad (número, menor = más importante): ")
                
                print("\n🔗 DEPENDENCIAS: Tareas que deben completarse antes.")
                print("Ejemplos:")
                print("  - Para 'Pintar pared', dependencias: 'Construir pared'")
                
                dependencias = input("\n📋 Dependencias (nombres separados por coma, Enter = ninguna): ")
                dependencias = [dep.strip() for dep in dependencias.split(',') if dep.strip()]

                deadline = input("\n⏳ Fecha de vencimiento (formato YYYY-MM-DD, Enter = sin vencimiento): ").strip()
                if deadline:
                    try:
                        datetime.strptime(deadline, "%Y-%m-%d")
                    except ValueError:
                        print("\n❌ Formato de fecha inválido. Usa el formato YYYY-MM-DD.")
                        continue
                
                task_manager.add_task(nombre, prioridad, dependencias, deadline)
            
            elif opcion == '2':
                if not task_manager.tasks:
                    print("\n📭 No hay tareas pendientes.")
                else:
                    print("\n📋 TAREAS PENDIENTES:")
                    for _, _, task in sorted(task_manager.tasks, key=lambda x: x[0]):
                        print(f"\n📍 {task['name']} (Prioridad: {task['priority']})")
                        if task['dependencies']:
                            print("   🔗 Dependencias:")
                            for dep in task['dependencies']:
                                print(f"     - {dep}")
                        if task.get('deadline'):
                            print(f"   ⏳ Fecha de vencimiento: {task['deadline']}")
            
            elif opcion == '3':
                nombre = input("\n✅ Nombre de la tarea a completar: ")
                task_manager.complete_task(nombre)
            
            elif opcion == '4':
                print("\n🔗 DEPENDENCIAS REGISTRADAS:")
                for tarea, dependientes in task_manager.task_dependencies.items():
                    print(f"\n📍 Tarea '{tarea}' es requerida para:")
                    for dep in dependientes:
                        print(f"   - {dep}")
            
            elif opcion == '5':
                task_manager.check_task_executability()
            
            elif opcion == '6':
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("Opción inválida.")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
