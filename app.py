from flask import Flask, render_template, jsonify, request
import enum
import time
import webbrowser
import threading
from typing import Optional, List, Dict, Tuple



class CellType(enum.Enum):
    PROBIRKA = "Пробирка"
    OBRABOTANO = "Обработано"
    RASTENIE = "Растение"
    LAB = "Лаб"
    FINISH = "Финиш"
    VODA = "Вода"
    CONTAINER = "Контейнер"



CELL_COLORS: Dict[CellType, str] = {
    CellType.PROBIRKA: "#ADD8E6",
    CellType.OBRABOTANO: "#90EE90",
    CellType.RASTENIE: "#3CB371",
    CellType.LAB: "#FF6347",  
    CellType.FINISH: "#FFA500",
    CellType.VODA: "#FFFFFF",
    CellType.CONTAINER: "#808080",  
}
CELL_TEXT: Dict[CellType, str] = {
    CellType.PROBIRKA: "ПРОБИРКА",
    CellType.OBRABOTANO: "ОБРАБ.",
    CellType.RASTENIE: "РАСТ.",
    CellType.LAB: "ЛАБ",
    CellType.FINISH: "ФИНИШ",
    CellType.VODA: "ВОДА",
    CellType.CONTAINER: "КОНТ.",
}

W, H = 5, 5


class Direction(enum.Enum):
    STEP_BIO = "БВперед"
    STEP_BACK = "БНазад"
    STEP_LEFT = "БВлево"
    STEP_RIGHT = "БВправо"



class RobotCell:
    def __init__(self, cell_type: CellType, x: int = 0, y: int = 0):
        self.cell_type: CellType = cell_type
        self.has_robot: bool = False
        self.x = x
        self.y = y

    def to_dict(self):
        """Сериализация клетки для передачи в JavaScript."""
        return {
            'x': self.x,
            'y': self.y,
            'type': self.cell_type.name,
            'color': CELL_COLORS[self.cell_type],
            'text': CELL_TEXT[self.cell_type],
            'has_robot': self.has_robot
        }


class RobotLabyrinth:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: List[List[RobotCell]] = [
            [RobotCell(CellType.VODA, x, y) for x in range(width)]
            for y in range(height)
        ]

    def initialize_labyrinth(self, default_type: CellType) -> None:
        for row in self.cells:
            for cell in row:
                cell.cell_type = default_type
                cell.has_robot = False

    def set_cell_type(self, x: int, y: int, cell_type: CellType) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x].cell_type = cell_type

    def initialize_mission_map(self):
        self.initialize_labyrinth(CellType.VODA)

        
        self.set_cell_type(4, 4, CellType.FINISH)
        self.set_cell_type(3, 4, CellType.LAB)
        self.set_cell_type(2, 4, CellType.CONTAINER)
        self.set_cell_type(1, 4, CellType.RASTENIE)

        
        self.set_cell_type(3, 3, CellType.RASTENIE)
        self.set_cell_type(1, 3, CellType.PROBIRKA)

        
        self.set_cell_type(3, 2, CellType.CONTAINER)
        self.set_cell_type(1, 2, CellType.RASTENIE)
        self.set_cell_type(0, 2, CellType.LAB)

        
        self.set_cell_type(2, 1, CellType.PROBIRKA)

        
        self.set_cell_type(4, 0, CellType.CONTAINER)
        self.set_cell_type(3, 0, CellType.LAB)

        self.cells[0][0].has_robot = True

    def serialize(self):
        """Возвращает список словарей для передачи в JSON."""
        return [
            [cell.to_dict() for cell in row]
            for row in self.cells
        ]


class RobotBiolog:
    def __init__(self, labyrinth: RobotLabyrinth):
        self.labyrinth = labyrinth
        self.action_history: List[str] = []

        self.current_cell: Optional[RobotCell] = self.labyrinth.cells[0][0]
        self.current_cell.has_robot = True

        self.current_x = 0
        self.current_y = 0
        self.moving_right = True

        self._log_action(f"Начало миссии в ({self.current_x},{self.current_y}).")

    def _log_action(self, action: str):
        timestamp = time.strftime("%H:%M:%S")
        self.action_history.append(f"[{timestamp}] {action}")

    def _move_robot(self, target: RobotCell) -> RobotCell:
        if not self.current_cell: raise Exception("Робот не находится в клетке!")

        self.current_cell.has_robot = False
        target.has_robot = True
        self.current_cell = target
        self.current_x = target.x
        self.current_y = target.y

        self._log_action(f"Перемещение: Шаг -> ({target.x},{target.y}). Тип: {target.cell_type.value}")
        return target

    def clear_plant(self) -> None:
        if self.current_cell and self.current_cell.cell_type == CellType.RASTENIE:
            self.current_cell.cell_type = CellType.PROBIRKA

    def prob(self) -> None:
        if self.current_cell and self.current_cell.cell_type == CellType.PROBIRKA:
            self.current_cell.cell_type = CellType.OBRABOTANO

    def process_current_cell(self) -> None:
        if not self.current_cell: return

        current_coords = f"({self.current_cell.x},{self.current_cell.y})"

        if self.current_cell.cell_type in (CellType.RASTENIE, CellType.PROBIRKA):
            if self.current_cell.cell_type == CellType.RASTENIE:
                self._log_action(f"В клетке {current_coords}: Найдено **Растение**. Обработка в Пробирку.")
                self.clear_plant()

            if self.current_cell.cell_type == CellType.PROBIRKA:
                self._log_action(f"В клетке {current_coords}: Найдена **Пробирка**. Обработка в Обработано.")
                self.prob()

        if self.current_cell.cell_type == CellType.FINISH:
            self._log_action(f"В клетке {current_coords}: Достигнут **Финиш**!")

    def is_mission_complete(self) -> bool:
        if not (self.current_x == W - 1 and self.current_y == H - 1): return False

        for row in self.labyrinth.cells:
            for cell in row:
                if cell.cell_type in (CellType.RASTENIE, CellType.PROBIRKA): return False

        return True

    def find_next_snake_move(self) -> Optional[RobotCell]:
        """Алгоритм движения "Змейка" строго по всем клеткам."""
        current_x, current_y = self.current_x, self.current_y

        
        dx = 1 if self.moving_right else -1
        next_x = current_x + dx

        if 0 <= next_x < W:
            return self.labyrinth.cells[current_y][next_x]

        
        if current_y < H - 1:
            next_y = current_y + 1
            self.moving_right = not self.moving_right
            return self.labyrinth.cells[next_y][current_x]

        return None

    def execute_single_step(self) -> bool:
        if self.is_mission_complete(): return False

        
        self.process_current_cell()

        
        next_cell = self.find_next_snake_move()

        if next_cell:
            self._move_robot(next_cell)

            
            if self.current_cell.cell_type in (CellType.LAB, CellType.CONTAINER):
                self._log_action(
                    f"Запрещено движение по клетке {self.current_cell.cell_type.value} в ({self.current_x},{self.current_y})!")

            return True
        else:
            if not self.is_mission_complete():
                self._log_action("Обход  завершен.")
            return False

    def get_state(self):
        """Возвращает текущее состояние для отправки клиенту."""
        return {
            'W': W,
            'H': H,
            'map': self.labyrinth.serialize(),
            'robot_x': self.current_x,
            'robot_y': self.current_y,
            'current_cell_type': self.current_cell.cell_type.name if self.current_cell else None,
            'history': self.action_history,
            'is_complete': self.is_mission_complete()
        }



app = Flask(__name__)

ROBOT_SIMULATOR: Optional[RobotBiolog] = None


def init_simulation():
    global ROBOT_SIMULATOR
    labyrinth = RobotLabyrinth(W, H)
    labyrinth.initialize_mission_map()
    robot = RobotBiolog(labyrinth)
    ROBOT_SIMULATOR = robot
    return robot


init_simulation()


HOST = '127.0.0.1'
PORT = 5000
URL = f"http://{HOST}:{PORT}"



def open_browser():
    time.sleep(1)
    webbrowser.open(URL)


@app.route('/')
def index():
    """Главная страница, загружает HTML-шаблон."""
    return render_template('index.html')


@app.route('/reset', methods=['POST'])
def reset_simulation():
    """Сбрасывает симуляцию и возвращает начальное состояние."""
    robot = init_simulation()
    return jsonify(robot.get_state())


@app.route('/step', methods=['POST'])
def execute_step():
    """Выполняет один шаг и возвращает новое состояние."""
    if ROBOT_SIMULATOR is None:
        init_simulation()

    success = ROBOT_SIMULATOR.execute_single_step()
    state = ROBOT_SIMULATOR.get_state()
    state['step_success'] = success
    return jsonify(state)


if __name__ == '__main__':
    print(f"Flask-сервер запускается на {URL}...")

    threading.Timer(1, open_browser).start()
    
    app.run(host=HOST, port=PORT, debug=True, use_reloader=False)
