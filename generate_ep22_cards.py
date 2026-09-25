import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.core.smart_card_generator import SmartCardGenerator

def generate_cards():
    gen = SmartCardGenerator()

    # --- VARIANT 1 ---
    v1_dir = BASE_DIR / "output" / "22" / "variant1" / "visuals"
    v1_dir.mkdir(parents=True, exist_ok=True)

    # Card 1: Scheme (Cutscene Invulnerability)
    gen.generate_diagram_card(
        output_path=v1_dir / "card1.png",
        title="СХЕМА: GODMODE В КАТ-СЦЕНЕ",
        badge="ЭТАП 1/2",
        step_title="Активация режима диалога",
        items=[
            "Запуск скрипта StartCutscene()",
            "Флаг персонажа: SetGodMode(true)",
            "Урон от внешних взрывов: 0 HP"
        ],
        accent_color="#38bdf8",
        footer_note="Сюжетные NPC защищены от любых внешних повреждений"
    )

    # Card 2: Code (Damage Filter vs Invulnerability)
    gen.generate_os_code_card(
        output_path=v1_dir / "card2.png",
        title="LS3D ENGINE SOLVER",
        file_tab="CutsceneManager.cpp",
        wrong_code=[
            "// ОШИБКА: Автомобиль получает урон и взрывается",
            "if (car.IsExploding()) { npc.TakeDamage(100); }"
        ],
        fixed_code=[
            "// ФИКС: Игнорирование радиуса взрыва в кат-сцене",
            "if (npc.IsInCutscene()) { return DAMAGE_NONE; }"
        ],
        takeaway="Бессмертие зафиксировано до конца реплики"
    )

    # --- VARIANT 2 ---
    v2_dir = BASE_DIR / "output" / "22" / "variant2" / "visuals"
    v2_dir.mkdir(parents=True, exist_ok=True)

    # Card 1: Scheme (Cutscene Locked State)
    gen.generate_diagram_card(
        output_path=v2_dir / "card1.png",
        title="СХЕМА: CUTSCENE LOCKED STATE",
        badge="ЭТАП 1/2",
        step_title="Защитный барьер геймдева",
        items=[
            "Вход в триггер разговора в гараже",
            "Блокировка State Machine: CUTSCENE_LOCKED",
            "Реакция на огненную коллизию: Игнор"
        ],
        accent_color="#fb923c",
        footer_note="Анимация речи имеет максимальный приоритет"
    )

    # Card 2: Code (Event Mask Filter)
    gen.generate_os_code_card(
        output_path=v2_dir / "card2.png",
        title="ACTOR EVENT MASK",
        file_tab="ActorStateSolver.cpp",
        wrong_code=[
            "// БАГ: Взрывная волна пытается вызвать деспавн",
            "on_explosion_event -> trigger_ragdoll_state();"
        ],
        fixed_code=[
            "// ПРАВИЛЬНО: Блокировка вызова рагдолла в кат-сцене",
            "if (state == CUTSCENE) -> ignore_event_call();"
        ],
        takeaway="Стейт-машина защищает персонажа от сброса"
    )

    # --- VARIANT 3 ---
    v3_dir = BASE_DIR / "output" / "22" / "variant3" / "visuals"
    v3_dir.mkdir(parents=True, exist_ok=True)

    # Card 1: Scheme (Independent Health Counters)
    gen.generate_diagram_card(
        output_path=v3_dir / "card1.png",
        title="СХЕМА: РАЗДЕЛЬНЫЕ СЧЕТЧИКИ HP",
        badge="ЭТАП 1/2",
        step_title="Расчет урона авто и NPC",
        items=[
            "Здоровье авто: Car.HP = 0 (Взрыв)",
            "Здоровье Ральфа: NPC.HP = 100/100",
            "Результат: Авто в хлам, Ральф невредим"
        ],
        accent_color="#4ade80",
        footer_note="Урон машины не передается находящемуся рядом NPC"
    )

    # Card 2: Code (Damage Evaluator)
    gen.generate_os_code_card(
        output_path=v3_dir / "card2.png",
        title="DAMAGE EVALUATOR",
        file_tab="HealthSystem.cpp",
        wrong_code=[
            "// ОШИБКА: Радиус взрыва авто ранит окружающих",
            "apply_blast_damage(radius, damage_val);"
        ],
        fixed_code=[
            "// ФИКС: Проверка флага invulnerable_cutscene",
            "if (npc.invulnerable_cutscene) { damage = 0; }"
        ],
        takeaway="Урон от машины обнуляется для квестовых персонажей"
    )

    print("[SUCCESS] All cards for Variant 1, 2, and 3 generated cleanly!")

if __name__ == "__main__":
    generate_cards()
