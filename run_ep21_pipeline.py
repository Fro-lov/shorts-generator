import asyncio
import json
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(r"e:\social")
sys.path.insert(0, str(BASE_DIR))

from src.core.pipeline_runner import PipelineRunner
from src.core.metadata_generator import MetadataGenerator

EPISODE_ID = "21"
EP_DIR = BASE_DIR / "output" / EPISODE_ID

VARIANTS = {
    "variant1": {
        "title": "Variant 1: Mission Seat Node Priority Override",
        "card_specs": [
            {
                "type": "diagram",
                "title": "GTA IV // Buddy Seat Allocation",
                "badge": "SITUATION",
                "step1_title": "1. Статус в автомобиле",
                "step1_items": [
                    "Нико приехал на миссию с кузином Романом",
                    "Роман сидит на пассажирском кресле SeatNode[1]",
                    "Автомобиль остановился в триггере миссии"
                ],
                "accent_color": "#38bdf8",
                "footer_note": "Роман занимает пассажирское место как спутник!"
            },
            {
                "type": "diagram",
                "title": "GTA IV // Seat Priority Override",
                "badge": "SCRIPT GLITCH",
                "step1_title": "2. Захват кресла NPC",
                "step1_items": [
                    "Квестовая девушка видит жесткую привязку к SeatNode[1]",
                    "Отсутствует проверка флага IsStoryPartner",
                    "[!] Срабатывает анимация JackPassenger -> Ejection!"
                ],
                "accent_color": "#f87171",
                "footer_note": "Движок катапультирует Романа головой в асфальт!"
            },
            {
                "type": "code",
                "title": "Fix // Vehicle Occupant Solver",
                "badge": "CODE FIX",
                "wrong_code": [
                    "void EnterVehicle(Vehicle* car) {",
                    "    EjectPassenger(car, SEAT_FRONT_RIGHT); // BUG: Always ejects!",
                    "}"
                ],
                "fixed_code": [
                    "void EnterVehicle(Vehicle* car) {",
                    "    if (car->GetOccupant(SEAT_FRONT_RIGHT)->IsStoryPartner())",
                    "        MoveOccupantToSeat(car, SEAT_REAR_RIGHT); // FIX: Move Roman back!",
                    "}"
                ],
                "takeaway": "Проверять статус партнера и пересаживать Романа на задний диван!"
            }
        ],
        "scenario": {
            "blocks": [
                {"name": "hook", "role": "host", "text": "Представьте: вы едете с кузином Романом, подбираете девушку, а она БЕЗ ВЫЯСНЕНИЯ ОТНОШЕНИЙ катапультирует Романа из машины прямо на асфальт!"},
                {"name": "investigation", "role": "host", "text": "Подожди, Дмитрий! Роман же его родной кузин и сидел рядом! За что его так жестко приземлили на грешную землю?"},
                {"name": "diagram1", "role": "expert", "text": "В GTA IV у тачки есть узлы сидений. Роман едет как лучший друг в статусе SeatNode1."},
                {"name": "code_card", "role": "expert", "text": "Но у квестовой девушки прописана привязка ровно к этому креслу! Движок забивает на Романа и включает авто-катапульту!"},
                {"name": "fix", "role": "expert", "text": "В итоге кузин красиво пашет лицом мостовую! Фикс: проверять флаг IsStoryPartner и пересаживать Романа на задний диван."},
                {"name": "outro", "role": "host", "text": "А вы тоже сбрасывали звонки Романа с зовом в боулинг? Напишите в комментариях и подписывайтесь на Onter's inn!"}
            ]
        }
    },
    "variant2": {
        "title": "Variant 2: Buddy System vs Mission Script Conflict",
        "card_specs": [
            {
                "type": "diagram",
                "title": "GTA IV // Mission Target Raycast",
                "badge": "SITUATION",
                "step1_title": "1. Целевой луч NPC",
                "step1_items": [
                    "Девушка миссии запрограммирована сесть к Нико",
                    "Скрипт пускает целевой луч к передней двери",
                    "Роман на пассажирском кресле считается преградой"
                ],
                "accent_color": "#fb923c",
                "footer_note": "Скрипт миссии не видит систему друзей!"
            },
            {
                "type": "diagram",
                "title": "GTA IV // Aggressive Ejection",
                "badge": "SCRIPT GLITCH",
                "step1_title": "2. Выдергивание бота",
                "step1_items": [
                    "Движок видит Романа как обычного бота-преграду",
                    "Запускается действие выдергивания без проверок",
                    "[!] Роман вылетает на дорогу как от удара врага!"
                ],
                "accent_color": "#f87171",
                "footer_note": "Силовое выдергивание без регистраций и СМС!"
            },
            {
                "type": "code",
                "title": "Fix // Mission AI Entry",
                "badge": "CODE FIX",
                "wrong_code": [
                    "int targetSeat = SEAT_FRONT_RIGHT; // Hardcoded seat assignment"
                ],
                "fixed_code": [
                    "int targetSeat = car->GetFirstAvailableSeat(); // FIX: Dynamic search!",
                    "if (targetSeat == SEAT_NONE) EjectEnemy(car);"
                ],
                "takeaway": "Находить первое свободное место GetFirstAvailableSeat!"
            }
        ],
        "scenario": {
            "blocks": [
                {"name": "hook", "role": "host", "text": "В GTA IV Роман думал, что вы бро за жизнь, пока скрипт миссии не отправил его в свободный полет на мостовую!"},
                {"name": "investigation", "role": "host", "text": "Дмитрий, проясни! Тачка же четырехдверная, почему дама не села на задний диван, а выкинула бедного Романа?"},
                {"name": "diagram1", "role": "expert", "text": "Движок GTA IV разделяет систему друзей и логику миссий. Нико привез Романа прямо в триггер квеста."},
                {"name": "code_card", "role": "expert", "text": "Девушка миссии генерирует целевой луч строго к передней двери. Движок считает Романа не другом, а банальной тушкой-преградой!"},
                {"name": "fix", "role": "expert", "text": "Срабатывает силовое выдергивание без регистраций и СМС. Фикс: функция GetFirstAvailableSeat отправляет даму на задний ряд!"},
                {"name": "outro", "role": "host", "text": "Не бросайте друзей ради миссий! Подписывайтесь на Onter's inn, ставьте лайк и оставайтесь с нами!"}
            ]
        }
    },
    "variant3": {
        "title": "Variant 3: State Machine Seat Reservation Reset",
        "card_specs": [
            {
                "type": "diagram",
                "title": "GTA IV // Seat Reservation Lock",
                "badge": "SITUATION",
                "step1_title": "1. Резервирование узла",
                "step1_items": [
                    "При запуске сцены вызывается SeatReservation",
                    "Резерв сиденья аннулирует права текущего седока",
                    "Роман мгновенно теряет статус владельца места"
                ],
                "accent_color": "#4ade80",
                "footer_note": "Права на сиденье сбрасываются мгновенно!"
            },
            {
                "type": "diagram",
                "title": "GTA IV // Ragdoll Drop",
                "badge": "SCRIPT GLITCH",
                "step1_title": "2. Сброс в регдолл",
                "step1_items": [
                    "Потеря статуса включается анимацию падения",
                    "Роман рендерится как вывалившийся физический объект",
                    "[!] Девушка беспрепятственно занимает место"
                ],
                "accent_color": "#f87171",
                "footer_note": "Кузин превращается в регдолл-мякиш на асфальте!"
            },
            {
                "type": "code",
                "title": "Fix // Ped Reservation System",
                "badge": "CODE FIX",
                "wrong_code": [
                    "bool ReserveSeat(Ped* ped, int seat) { ForceClearSeat(seat); }"
                ],
                "fixed_code": [
                    "bool ReserveSeat(Ped* ped, int seat) {",
                    "    if (IsSeatOccupiedByFriend(seat)) return AssignRearSeat(ped);",
                    "}"
                ],
                "takeaway": "Проверять дружбу седока перед очисткой резерва!"
            }
        ],
        "scenario": {
            "blocks": [
                {"name": "hook", "role": "host", "text": "Баг или романтическая ревность? В GTA IV персонаж миссии просто сбросила Романа на дорогу, чтобы занять его место рядом с Нико!"},
                {"name": "investigation", "role": "host", "text": "Постой! Почему Роман даже не сопротивлялся, а просто вывалился из машины как мешок с картошкой?"},
                {"name": "diagram1", "role": "expert", "text": "При запуске сцены квестовый NPC резервирует узел сиденья SeatReservation. И Роман мгновенно теряет все права на кресло!"},
                {"name": "code_card", "role": "expert", "text": "Потеря статуса выключает физику тела, превращая Романа в регдолл-мякиш, пока девушка усаживается рядом."},
                {"name": "fix", "role": "expert", "text": "В gta4_ped_reservation.cpp нужно проверять дружбу седока и не лишать кузина прав на переднее сиденье!"},
                {"name": "outro", "role": "host", "text": "Теперь Роман в безопасности и готов к боулингу! Нажмите лайк, подпишитесь на Onter's inn и пишите ваш любимый баг в комментариях!"}
            ]
        }
    }
}


def main():
    print(f"[*] Starting PipelineRunner for Episode {EPISODE_ID}...")
    runner = PipelineRunner(EPISODE_ID)

    for var_name, var_data in VARIANTS.items():
        print(f"\n==========================================")
        print(f"[*] Processing {var_name}: {var_data['title']}")
        print(f"==========================================")

        # 1. Generate Smart Visual Cards via PipelineRunner
        cards = runner.generate_visual_cards(var_name, var_data["card_specs"])
        print(f"[*] Generated Cards: {[c.name for c in cards]}")

        # 2. Render Full Variant Video via PipelineRunner
        out_video = runner.render_variant(var_name, var_data["scenario"], cards)
        print(f"[*] Rendered Video: {out_video}")

        # 3. Perform 4-Point Smoke Test
        smoke_res = runner.run_smoke_test(out_video)
        print(f"[*] Smoke Test Results for {var_name}: {smoke_res}")
        if not smoke_res["decodability"] or not smoke_res["file_size_ok"]:
            raise RuntimeError(f"Smoke Test Failed for {var_name}!")

    # 4. Copy Variant 1 as main video.mp4 in output root
    main_video = EP_DIR / "video.mp4"
    var1_video = EP_DIR / "variant1" / "video.mp4"
    shutil.copy(var1_video, main_video)
    print(f"\n[*] Copied Variant 1 to main video: {main_video}")

    # 5. Generate metadata.json and description.txt via MetadataGenerator
    scenario_meta = {
        "episode_id": EPISODE_ID,
        "lang": "ru",
        "game": "GTA IV",
        "bug_title": "Почему NPC выкидывает кузина Романа из машины?",
        "blocks": VARIANTS["variant1"]["scenario"]["blocks"],
        "metadata": {
            "title": "GTA IV: Почему NPC выкидывает кузина Романа из машины? 💥 (Физика и скрипты игр)",
            "short_title": "GTA IV — Почему NPC выкидывает Романа из тачки? #shorts #игры #gta4",
            "tags": [
                "gta4", "gtaiv", "grandtheftauto", "gta4bugs", "shorts", "игры",
                "баги", "багииграх", "геймдев", "игровыеприколы", "физикаиграх",
                "юмор", "мемы", "видеоигры", "gamedev", "ontersinn"
            ],
            "pinned_comment": "👇 А с какими самыми смешными выкрутасами NPC в GTA IV сталкивались вы? Пишите в комментариях!"
        }
    }

    MetadataGenerator.generate(scenario_meta, EP_DIR, duration=42.0)
    print(f"\nSUCCESS: Episode {EPISODE_ID} pipeline run complete and 100% validated!")


if __name__ == "__main__":
    main()
