from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RiskBand(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ActionType(str, Enum):
    OPEN_EXIT = "open_exit"
    CLOSE_EXIT = "close_exit"
    DEPLOY_GUARDS = "deploy_guards"
    REDIRECT_ZONE = "redirect_zone"
    ACTIVATE_PA = "activate_pa"
    DEPLOY_MEDICAL = "deploy_medical"
    ROUTE_EVACUATION = "route_evacuation"
    HOLD_INGRESS = "hold_ingress"


class ZoneRef(BaseModel):
    id: UUID
    code: str
    name: str
    area_m2: float
    capacity: int


class ZoneMetrics(BaseModel):
    zone_id: UUID
    timestamp: float
    count: int
    density: float
    mean_speed: float
    opposing_flow: float
    group_cohesion: float
    abnormal_motion: float
    exit_pressure: float
    weather_factor: float = 0.0
    time_prior: float = 0.0
    historical_hotspot: float = 0.0
    emergency_flag: float = 0.0
    forecast_surge: float = 0.0


class RiskScore(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    zone_id: UUID
    timestamp: float
    dcrs: float
    band: RiskBand
    horizon_minutes: int = 0
    forecast_dcrs: Optional[float] = None


class FeatureContribution(BaseModel):
    feature: str
    value: float
    weight: float
    contribution: float


class RiskExplanation(BaseModel):
    risk_id: UUID
    zone_id: UUID
    dcrs: float
    contributions: list[FeatureContribution]
    narrative: str


class DecisionAction(BaseModel):
    action_type: ActionType
    title: str
    payload: dict[str, Any]
    priority: int = 1
    confidence: float = 0.8
    status: str = "pending"  # pending | accepted | dismissed


class DecisionBundle(BaseModel):
    alert_id: UUID
    zone_id: UUID
    dcrs: float
    actions: list[DecisionAction]
    rationale: str


class SimulationScenario(BaseModel):
    name: str
    close_exits: list[str] = []
    rainfall_mm_h: float = 0.0
    vip_zone: Optional[str] = None
    hold_ingress: bool = False
    horizon_minutes: int = 10


class SimulationResult(BaseModel):
    scenario: SimulationScenario
    predicted_peak_dcrs: float
    baseline_peak_dcrs: float = 0.0
    dcrs_delta: float = 0.0
    congested_zones: list[str]
    recommended_actions: list[DecisionAction]
    narrative: str
    zone_risks: list[dict[str, Any]] = []
    simulation_id: Optional[str] = None
    generated_at: Optional[float] = None
