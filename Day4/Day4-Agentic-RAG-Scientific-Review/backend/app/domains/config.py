from dataclasses import dataclass


@dataclass(frozen=True)
class DomainConfig:
    id: str
    name: str
    description: str
    system_prompt_suffix: str
    example_questions: list[str]


DOMAIN_REGISTRY: dict[str, DomainConfig] = {
    "logistics": DomainConfig(
        id="logistics",
        name="Logistics",
        description="Pharmaceutical supply-chain, cold-chain, and drug-distribution logistics.",
        system_prompt_suffix=(
            "You are focused on pharmaceutical supply-chain and drug-distribution logistics: "
            "cold-chain integrity, last-mile distribution, inventory/demand forecasting for "
            "medicines, and supply-chain resilience. Prefer arXiv for operations-research and "
            "optimization methodology (categories like math.OC, stat.AP), and PubMed for "
            "health-system logistics and cold-chain/vaccine-distribution studies."
        ),
        example_questions=[
            "What methods improve cold-chain integrity for vaccine distribution in low-resource settings?",
            "What operations-research approaches reduce stockouts of essential medicines?",
        ],
    ),
    "healthcare": DomainConfig(
        id="healthcare",
        name="Healthcare",
        description="General healthcare delivery, health systems, and clinical practice literature.",
        system_prompt_suffix=(
            "You are focused on healthcare delivery, health systems research, and clinical "
            "practice. Prefer PubMed for clinical and health-services literature; use arXiv "
            "for computational or quantitative health methods when relevant."
        ),
        example_questions=[
            "What are effective interventions for reducing hospital readmission rates?",
            "How is telemedicine affecting patient outcomes in rural healthcare?",
        ],
    ),
    "clinical_trials_stats": DomainConfig(
        id="clinical_trials_stats",
        name="Clinical Trials Statistics",
        description="Biostatistics and study design for clinical trials.",
        system_prompt_suffix=(
            "You are focused on clinical trial design and biostatistics: adaptive trial "
            "designs, sample-size and power analysis, interim analysis, and statistical "
            "methodology. Treat arXiv categories stat.ME and stat.AP as first-class sources "
            "alongside PubMed for methodology and applied clinical statistics."
        ),
        example_questions=[
            "What are the statistical advantages of adaptive trial designs over fixed designs?",
            "How is sample size determined for non-inferiority trials?",
        ],
    ),
    "pharmacovigilance": DomainConfig(
        id="pharmacovigilance",
        name="Pharmacovigilance / Drug Safety",
        description="Adverse event monitoring, drug safety signals, and post-market surveillance.",
        system_prompt_suffix=(
            "You are focused on pharmacovigilance and drug safety: adverse event reporting, "
            "signal detection, post-market surveillance, and drug-drug interactions. Prefer "
            "PubMed for adverse-event and clinical safety literature; use arXiv for "
            "statistical signal-detection methodology when relevant."
        ),
        example_questions=[
            "What are recent signals of hepatotoxicity associated with GLP-1 receptor agonists?",
            "What statistical methods are used for adverse-event signal detection in spontaneous reporting systems?",
        ],
    ),
}


def get_domain(domain_id: str) -> DomainConfig | None:
    return DOMAIN_REGISTRY.get(domain_id)


def list_domains() -> list[DomainConfig]:
    return list(DOMAIN_REGISTRY.values())
