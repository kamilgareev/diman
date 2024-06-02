from typing import List

import aiohttp
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import numpy as np
import matplotlib.pyplot as plt

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/plots", StaticFiles(directory="plots"), name="plots")

plot_number = 0


class Roots(BaseModel):
    roots: List[int]


@app.get('/solve', response_model=Roots)
async def solve(a: int, b: int, c: int):
    discriminant = b ** 2 - 4 * a * c

    if discriminant > 0:
        root2 = (-b - np.sqrt(discriminant)) / (2 * a)
        root1 = (-b + np.sqrt(discriminant)) / (2 * a)
        roots = sorted([root1, root2])
    elif discriminant == 0:
        root = -b / (2 * a)
        roots = [root]
    else:
        roots = []

    return {"roots": roots}


@app.get("/main", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/plot", response_class=HTMLResponse)
async def plot_graph(request: Request, a: int = Form(...), b: int = Form(...), c: int = Form(...)):
    plt.style.use('ggplot')

    x = np.linspace(-5, 5, 500)
    y = a * x ** 2 + b * x + c
    plt.figure(figsize=(10, 5))
    plt.plot(x, y, label=f"{a}x² + {b}x + {c}")

    global plot_number
    plot_path = f"plots/plot{plot_number}.png"
    plot_number += 1

    async with aiohttp.ClientSession() as session:
        response = await session.get(f'http://127.0.0.1:8000/solve?a={a}&b={b}&c={c}')
        roots_json = await response.json()
        roots = roots_json['roots']
        for root in roots:
            plt.plot(root, 0, marker='o', color='blue')

    plt.legend()
    plt.savefig(plot_path)

    return templates.TemplateResponse("form.html", {"request": request,
                                                    "plot_path": plot_path,
                                                    "roots": roots})
