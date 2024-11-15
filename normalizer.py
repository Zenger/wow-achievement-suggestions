# SPDX-License-Identifier: MIT
import json

from pydantic import BaseModel, ValidationError
from typing import List, Optional

from pydantic import BaseModel
from typing import List, Optional


class Achievement(BaseModel):
    name: str
    id: int


class ChildCriterum(BaseModel):
    id: int
    description: str
    amount: int
    achievement: Optional[Achievement]  # Correct usage of Optional


class Operator(BaseModel):
    type: str
    name: str


class Criteria(BaseModel):
    id: int
    description: str
    amount: int
    operator: Operator
    child_criteria: List[ChildCriterum]


class AchievementResponse(BaseModel):
    id: int
    name: str
    description: str
    points: int
    is_account_wide: bool
    criteria: Criteria


class AchievementNormalizer:
    def __init__(self, data):
        try:
            self.normalized = AchievementResponse.parse_obj(data)
        except ValidationError as e:
            print("Validation error during normalization:", e.json())
            self.normalized = None  # Ensures that if parsing fails, normalized is explicitly set to None

    def get_data(self):
        return self.normalized  # Returns None if parsing failed, be mindful when using this method

    def has_child_criteria(self):
        return self.normalized is not None and bool(self.normalized.criteria.child_criteria)

    def to_dict(self):
        if self.normalized is not None:
            return self.normalized.dict()
        return {}  # Return empty dict if no data was normalized

    def __str__(self):
        if self.normalized is not None:
            return json.dumps(self.to_dict(), indent=2)
        return "{}"  # Return empty JSON string if no data


class ICharacterAchievementCriteria(BaseModel):
    id: int
    amount: int | None
    is_complete: bool


class ICharacterAchievementCriteriaParentObject(BaseModel):
    id: int
    is_complete: bool
    child_criteria: List[ICharacterAchievementCriteria] | None


class ICharacterAchievementDetailed(BaseModel):
    name: str


class ICharacterAchievement(BaseModel):
    id: int
    achievement: ICharacterAchievementDetailed | None
    criteria: ICharacterAchievementCriteriaParentObject | None
    completed_timestamp: str | int | None


class ICharacterAchievementObject(BaseModel):
    achievements: List[ICharacterAchievement]


class CharacterAchievements:
    normalized = None

    def __init__(self, data):
        achievements = []
        if data.get('achievements'):
            for achievement in data.get('achievements'):
                achievement_data = None
                criteria_data = None
                if achievement.get('achievement'):
                    achievement_data = ICharacterAchievementDetailed(
                        name=achievement['achievement']['name']
                    )
                if achievement.get('criteria'):
                    is_completed = achievement.get('completed_timestamp') is not None
                    if achievement.get('criteria').get('child_criteria'):
                        child_criteria = []
                        for criteria in achievement['criteria']['child_criteria']:
                            child_criteria.append(
                                ICharacterAchievementCriteria(
                                    id=criteria['id'],
                                    amount=criteria.get('amount'),
                                    is_complete=is_completed
                                )
                            )
                        criteria_data = ICharacterAchievementCriteriaParentObject(
                            id=achievement['criteria']['id'],
                            is_complete=is_completed,
                            child_criteria=child_criteria
                        )
                achievements.append(
                    ICharacterAchievement(
                        id=achievement['id'],
                        achievement=achievement_data,
                        criteria=criteria_data,
                        completed_timestamp=achievement.get('completed_timestamp')
                    )
                )

        self.normalized = ICharacterAchievementObject(achievements=achievements)

    def get_data(self):
        return self.normalized

    def to_dict(self):
        return self.normalized.dict()


class Normalizer:
    def __init__(self):
        pass

    def from_achievement(self, data: dict):
        return AchievementNormalizer(data)

    def character_achievements(self, data: dict):
        return CharacterAchievements(data)
