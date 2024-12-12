# from fastapi import FastAPI, Request, Form
# from fastapi.responses import RedirectResponse
# from fastapi.templating import Jinja2Templates
#
# from models import Secret, SecretForm
#
#
# @app.post("/secret/")
# async def create_secret(request: Request, title: str = Form(...), content: str = Form(...)):
#     # Создаем экземпляр модели Secret
#     secret = Secret(title=title, content=content)
#     # Сохраняем секрет в базу данных (например, через SQLAlchemy)
#     db_session.add(secret)
#     db_session.commit()
#
#     # Перенаправляем на страницу списка секретов
#     return RedirectResponse(url="/secrets/", status_code=303)
#
#
# @app.get("/secrets/")
# async def list_secrets(request: Request):
#     # Получаем все секреты из базы данных
#     secrets = db_session.query(Secret).order_by(Secret.created_at.desc()).all()
#
#     # Рендерим шаблон с формой и списком секретов
#     return templates.TemplateResponse("secret.html", {"request": request, "form": SecretForm(), "secrets": secrets})