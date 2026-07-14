from pathlib import Path

from aiogram.fsm.context import FSMContext

from app.services.file_service import delete_file


async def cleanup_state_files(state: FSMContext) -> None:
    data = await state.get_data()

    file_path = data.get("file_path")
    output_file_path = data.get("output_file_path")

    if file_path:
        delete_file(Path(file_path))
    if output_file_path:
        delete_file(Path(output_file_path))
