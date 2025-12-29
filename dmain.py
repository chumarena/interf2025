import enum
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
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

CELL_SIZE = 80

ROBOT_COLOR = "#0000FF"


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


class RobotLabyrinth:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells: List[List[RobotCell]] = [
            [RobotCell(CellType.VODA, x, y) for x in range(width)]
            for y in range(height)
        ]

    def initialize_labyrinth(self, default_type: CellType) -> None:
        """Инициализация лабиринта дефолтным типом."""
        for row in self.cells:
            for cell in row:
                cell.cell_type = default_type
                cell.has_robot = False

    def set_cell_type(self, x: int, y: int, cell_type: CellType) -> None:
        """Устанавливает тип ячейки по координатам (x, y)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x].cell_type = cell_type

    def initialize_mission_map(self):
        """Конкретная инициализация карты 5x5 для миссии."""
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
        """Вспомогательный метод для записи действия с временной меткой."""
        timestamp = time.strftime("%H:%M:%S")
        self.action_history.append(f"[{timestamp}] {action}")

    def _move_robot(self, target: RobotCell) -> RobotCell:
        """Внутренний метод для перемещения робота в указанную клетку."""
        if not self.current_cell:
            raise Exception("Робот не находится в клетке!")

        self.current_cell.has_robot = False
        target.has_robot = True
        self.current_cell = target
        self.current_x = target.x
        self.current_y = target.y

        self._log_action(f"Перемещение: Шаг -> ({target.x},{target.y}). Тип: {target.cell_type.value}")
        return target

    def clear_plant(self) -> None:
        """Обработка Растение -> Пробирка"""
        if self.current_cell and self.current_cell.cell_type == CellType.RASTENIE:
            self.current_cell.cell_type = CellType.PROBIRKA

    def prob(self) -> None:
        """Обработка Пробирка -> Обработано"""
        if self.current_cell and self.current_cell.cell_type == CellType.PROBIRKA:
            self.current_cell.cell_type = CellType.OBRABOTANO

    def process_current_cell(self) -> None:
        """Обрабатывает текущую клетку согласно правилам."""
        if not self.current_cell: return

        current_coords = f"({self.current_cell.x},{self.current_cell.y})"


        if self.current_cell.cell_type in (CellType.LAB, CellType.CONTAINER):
            return

        if self.current_cell.cell_type == CellType.RASTENIE:
            self._log_action(f"В клетке {current_coords}: Найдено **Растение**. Обработка в Пробирку.")
            self.clear_plant()

        if self.current_cell.cell_type == CellType.PROBIRKA:
            self._log_action(f"В клетке {current_coords}: Найдена **Пробирка**. Обработка в Обработано.")
            self.prob()

        if self.current_cell.cell_type == CellType.FINISH:
            self._log_action(f"В клетке {current_coords}: Достигнут **Финиш**!")

    def is_mission_complete(self) -> bool:
        """Проверка завершения миссии: Финиш достигнут И нет необработанных клеток."""

        if not (self.current_x == W - 1 and self.current_y == H - 1):
            return False

        for row in self.labyrinth.cells:
            for cell in row:
                if cell.cell_type in (CellType.RASTENIE, CellType.PROBIRKA):
                    return False

        return True

    def find_next_snake_move(self) -> Optional[RobotCell]:

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
        """Один шаг миссии: обработка + движение по змейке."""
        if self.is_mission_complete(): return False


        self.process_current_cell()


        next_cell = self.find_next_snake_move()

        if next_cell:
            self._move_robot(next_cell)


            if self.current_cell.cell_type in (CellType.LAB, CellType.CONTAINER):
                self._log_action(
                    f" Запрещено движение по клетке {self.current_cell.cell_type.value} в ({self.current_x},{self.current_y}) !")

            return True
        else:
            if not self.is_mission_complete():
                self._log_action("Обход 'Змейка' завершен.")
            return False

    def run_mission(self, update_callback):
        """Автозапуск с колбэком для обновления GUI."""
        if self.is_mission_complete(): return

        self._log_action("--- НАЧАЛО АВТОЗАПУСКА (Змейка) ---")

        def auto_step():
            if self.is_mission_complete():
                self._log_action("--- АВТОЗАПУСК ЗАВЕРШЕН ---")
                update_callback()
                return

            if self.execute_single_step():
                update_callback()
                self.labyrinth.root.after(300, auto_step)
            else:
                self._log_action("Автозапуск остановлен.")
                update_callback()

        if hasattr(self.labyrinth, 'root'):
            auto_step()




class RobotApp:
    def __init__(self, master):
        self.master = master
        master.title("Robot Biolog Labyrinth ")

        self.labyrinth = RobotLabyrinth(W, H)
        self.labyrinth.initialize_mission_map()
        self.robot = RobotBiolog(self.labyrinth)
        self.labyrinth.root = master
        self.robot_oval = None

        main_frame = tk.Frame(master)
        main_frame.pack(padx=10, pady=10)

        
        map_frame = tk.LabelFrame(main_frame, text="Карта 5x5 ", padx=5, pady=5)
        map_frame.pack(side=tk.LEFT, padx=10)

        canvas_width = W * CELL_SIZE + 50
        canvas_height = H * CELL_SIZE + 50
        self.canvas = tk.Canvas(map_frame, width=canvas_width, height=canvas_height, bg="lightgrey")
        self.canvas.pack()

        self.draw_map_elements()

        
        control_frame = tk.Frame(main_frame)
        control_frame.pack(side=tk.RIGHT, padx=10, fill=tk.Y)

        
        button_frame = tk.LabelFrame(control_frame, text="Управление", padx=10, pady=10)
        button_frame.pack(pady=10, fill=tk.X)

        self.btn_auto = tk.Button(button_frame, text="Автозапуск", command=self.run_auto, width=25)
        self.btn_auto.pack(pady=5)

        self.btn_step = tk.Button(button_frame, text="Один шаг", command=self.run_step, width=25)
        self.btn_step.pack(pady=5)

        tk.Button(button_frame, text="Сброс", command=self.reset_app, width=25).pack(pady=5)

        # История действий
        history_frame = tk.LabelFrame(control_frame, text="История Действий", padx=5, pady=5)
        history_frame.pack(expand=True, fill=tk.BOTH)

        self.history_text = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, height=18, width=35,
                                                      state='disabled', font=('Courier', 9))
        self.history_text.pack(expand=True, fill=tk.BOTH)

        self.update_display()

    def get_canvas_coords(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """Преобразует координаты (x, y) лабиринта в координаты пикселей Canvas."""


        canvas_y = H - 1 - y

        x1 = x * CELL_SIZE + 25
        y1 = canvas_y * CELL_SIZE + 25
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        return x1, y1, x2, y2

    def draw_map_elements(self):
        """Отрисовывает статические элементы карты (сетку, подписи, текст клеток)."""
        self.canvas.delete("all")


        for y in range(H):
            for x in range(W):
                x1, y1, x2, y2 = self.get_canvas_coords(x, y)
                cell = self.labyrinth.cells[y][x]

                self.canvas.create_rectangle(x1, y1, x2, y2,
                                             fill=CELL_COLORS[cell.cell_type],
                                             outline="black", width=1)


                self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2,
                                        text=CELL_TEXT[cell.cell_type],
                                        font=("Arial", 8, "bold"),
                                        fill='black')


        for x in range(W):
            self.canvas.create_text(x * CELL_SIZE + 25 + CELL_SIZE / 2, 10, text=f"X={x}", fill='black')
        for y in range(H):
            self.canvas.create_text(15, (H - 1 - y) * CELL_SIZE + 25 + CELL_SIZE / 2, text=f"Y={y}", fill='black')

    def update_display(self):
        """Обновляет карту и историю действий."""


        self.draw_map_elements()


        x_robot, y_robot = self.robot.current_x, self.robot.current_y
        current_cell_type = self.labyrinth.cells[y_robot][x_robot].cell_type


        if current_cell_type not in (CellType.LAB, CellType.CONTAINER):

            x1, y1, x2, y2 = self.get_canvas_coords(x_robot, y_robot)
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            radius = 20

            self.robot_oval = self.canvas.create_oval(center_x - radius, center_y - radius,
                                                      center_x + radius, center_y + radius,
                                                      fill=ROBOT_COLOR, outline="black", width=2)
        else:
            x1, y1, x2, y2 = self.get_canvas_coords(x_robot, y_robot)
            self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3, tags="robot_highlight")


        self.history_text.config(state='normal')
        self.history_text.delete('1.0', tk.END)
        for action in self.robot.action_history:
            self.history_text.insert(tk.END, action + '\n')
        self.history_text.see(tk.END)
        self.history_text.config(state='disabled')


        if self.robot.is_mission_complete():
            messagebox.showinfo("Миссия завершена", "Робот завершил обход  и обработал все клетки!")
            self.btn_auto.config(state=tk.DISABLED)
            self.btn_step.config(state=tk.DISABLED)

    def run_step(self):
        """Обработчик кнопки "Один шаг"."""
        self.robot.execute_single_step()
        self.update_display()

    def run_auto(self):
        """Обработчик кнопки "Автозапуск"."""
        self.btn_auto.config(state=tk.DISABLED)
        self.btn_step.config(state=tk.DISABLED)
        self.robot.run_mission(self.update_display)

    def reset_app(self):
        """Сброс состояния приложения."""
        self.labyrinth = RobotLabyrinth(W, H)
        self.labyrinth.initialize_mission_map()
        self.robot = RobotBiolog(self.labyrinth)
        self.labyrinth.root = self.master
        self.btn_auto.config(state=tk.NORMAL)
        self.btn_step.config(state=tk.NORMAL)
        self.update_display()
        self.history_text.config(state='normal')
        self.history_text.delete('1.0', tk.END)
        self.history_text.config(state='disabled')
        self.robot.action_history = []
        self.robot._log_action("Симулятор сброшен. Миссия началась снова.")
        self.update_display()


if __name__ == "__main__":
    root = tk.Tk()
    app = RobotApp(root)
    root.mainloop()