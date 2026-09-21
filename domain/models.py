import math
from datetime import datetime, timezone
from typing import List

class Review:

    def __init__(self, status: str, created_at: datetime):
        self.status = status
        self.created_at = created_at

class EcoPoint:
    def __init__(self, id: int, name: str, address: str, latitude: float, longitude: float, wastes: List[str], reviews: List[Review]):
        self.id = id
        self.name = name
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.wastes = wastes
        self.lambda_coef = 0.05
        self.reviews = reviews

    def math_model(self) -> int:
        if not self.reviews:
            return 100
        now = datetime.now(timezone.utc)

        a = 0 #копит взвешенные голоса пользователей
        b = 0 #сумма всех весов

        for review in self.reviews:
            time = (now - review.created_at ).total_seconds() / 3600.0
            weight_of_review = math.exp(-self.lambda_coef * time)

            if review.status == 'works':
                voices = 1.0
            else:
                voices = 0.0

            a += (voices * weight_of_review)
            b += weight_of_review

        if b == 0:
            return 100
        else:
            response = int((a / b)*100)
            return response

        

