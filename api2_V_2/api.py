from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import asyncio
import uvicorn
import json
import os

from page_requester import GoogleRequester
from page_parser import DekstopScrape
import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_counter():
    """Получает текущее значение счетчика из файла"""
    try:
        with open("counter_data/success_counter.txt", "r") as f:
            return int(f.read().strip())
    except:
        return 0

def increment_counter():
    """Увеличивает счетчик на 1 и записывает в файл"""
    counter = get_counter() + 1
    os.makedirs("counter_data", exist_ok=True)  # Создаем директорию, если ее нет
    with open("counter_data/success_counter.txt", "w") as f:
        f.write(str(counter))
    return counter

@app.get("/")
async def root():
    return {"status": "API is running"}


@app.get("/search")
async def search(
    query: str = Query(..., description="search query"),
    domain: Optional[str] = Query("google.com", description=" (google domain, example: google.com)"),
    num: Optional[int] = Query(10, description="quantity of results (10-100)"),
    gl: Optional[str] = Query('us', description="geo parametr (example, us, ru)"),
    hl: Optional[str] = Query('en', description="interface language (example, en, ru)"),
    lr: Optional[str] = Query('lang_en', description="language results (example, lang_en)"),
    cr: Optional[str] = Query(None, description="country (example, countryUS)"),
    location: Optional[str] = Query(None, description="location (example, 'New York,United States')"),
) -> Dict[str, Any]:
    
    try:
        # Инициализация GoogleRequester
        requester = GoogleRequester()
        
        # Выполнение поискового запроса
        result = await requester.search_google_async(
            query=query,
            domain=domain,
            num=num,
            gl=gl,
            hl=hl,
            lr=lr,
            cr=cr,
            location=location,
            test_pause=0  # Не используем паузу в API
        )
        
        # Если запрос не удался, возвращаем ошибку
        if not result["success"]:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": result["error"]
                }
            )
        
        if result.get("html"):
            try:
                scraper = DekstopScrape()
                parsed_data = await scraper.make_json(result["html"])
                
                clean_result = {
                "success": result["success"],
                "parsed_data": parsed_data,
                "organic_count": len(parsed_data.get("organic", [])),
                "ads_count": len(parsed_data.get("ads", []))
            }

                increment_counter()
                return clean_result
            
            except Exception as e:
                # В случае ошибки парсинга, добавляем информацию об ошибке
                increment_counter()
                return {
                "success": False,
                "error": f"Ошибка при парсинге результатов: {str(e)}"
            }

                
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error while searching: {str(e)}"
        )
    

@app.get("/counter")
async def counter():
    """Возвращает текущее значение счетчика успешных запросов"""
    return {"total_requests": get_counter()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)