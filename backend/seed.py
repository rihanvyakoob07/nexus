"""
Seed script: generates ~60 synthetic engineers + ~20 client JDs.
Run: python seed.py  (from backend/ directory)
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone
from app.core.db import init_db, AsyncSessionLocal
from app.core.security import hash_password
from app.models.engineer import Engineer, Skill, EngineerSkill, Evidence
from app.models.project import Project, Certification
from app.models.jd import JD, JDCapability
from app.services.confidence_scoring import compute_confidence

SKILLS = [
    # Agentic AI
    ("RAG Systems", "Agentic AI"),
    ("Agentic AI Frameworks", "Agentic AI"),
    ("LangChain", "Agentic AI"),
    ("LlamaIndex", "Agentic AI"),
    ("Prompt Engineering", "Agentic AI"),
    ("OpenAI API", "Agentic AI"),
    ("Anthropic Claude API", "Agentic AI"),
    ("Tool Use & Function Calling", "Agentic AI"),
    ("Multi-Agent Orchestration", "Agentic AI"),
    ("Memory & State Management", "Agentic AI"),
    ("LLM Guardrails & Safety", "Agentic AI"),
    ("AutoGen / CrewAI", "Agentic AI"),
    # ML Engineering
    ("Fine-tuning LLMs", "ML Engineering"),
    ("MLOps", "ML Engineering"),
    ("Evaluation & Benchmarking", "ML Engineering"),
    ("Cost Optimisation", "ML Engineering"),
    ("Hugging Face", "ML Engineering"),
    ("Model Quantisation", "ML Engineering"),
    ("RLHF & Preference Data", "ML Engineering"),
    ("Experiment Tracking (MLflow/W&B)", "ML Engineering"),
    # Cloud AI
    ("Azure AI Services", "Cloud AI"),
    ("AWS Bedrock", "Cloud AI"),
    ("Google Vertex AI", "Cloud AI"),
    ("Azure OpenAI Service", "Cloud AI"),
    ("AWS SageMaker", "Cloud AI"),
    # Data Infrastructure
    ("Vector Databases", "Data Infrastructure"),
    ("Embeddings & Retrieval", "Data Infrastructure"),
    ("Semantic Search", "Data Infrastructure"),
    ("Data Engineering", "Data Infrastructure"),
    ("Knowledge Graph Integration", "Data Infrastructure"),
    ("Streaming Data (Kafka/Kinesis)", "Data Infrastructure"),
    ("PostgreSQL / pgvector", "Data Infrastructure"),
    # Engineering
    ("Python", "Engineering"),
    ("FastAPI", "Engineering"),
    ("TypeScript / Node.js", "Engineering"),
    ("React / Next.js", "Engineering"),
    ("REST API Design", "Engineering"),
    ("GraphQL", "Engineering"),
    # DevOps
    ("Docker & Kubernetes", "DevOps"),
    ("CI/CD Pipelines", "DevOps"),
    ("Terraform / IaC", "DevOps"),
    ("Observability & Monitoring", "DevOps"),
    # Architecture
    ("System Design", "Architecture"),
    ("Distributed Systems", "Architecture"),
    ("Microservices Architecture", "Architecture"),
    ("Event-Driven Architecture", "Architecture"),
    # Security
    ("Security & Compliance", "Security"),
    ("Data Privacy & GDPR", "Security"),
    ("Zero Trust Architecture", "Security"),
    # Delivery
    ("Client Communication", "Delivery"),
    ("Technical Leadership", "Delivery"),
    ("Agile Delivery", "Delivery"),
    ("Stakeholder Management", "Delivery"),
]

SENIORITIES = ["junior", "mid", "senior", "principal"]

SENIORITY_WEIGHTS = [0.15, 0.35, 0.35, 0.15]  # Realistic distribution

JD_TEMPLATES = [
    {
        "client_name": "Accenture",
        "raw_text": (
            "We need a senior AI engineer to build an enterprise RAG system for document intelligence "
            "across legal and compliance workflows. Must have strong hands-on experience in LangChain, "
            "Azure AI Services, vector databases, and production deployment at scale. Experience with "
            "security and compliance in regulated industries is required. Technical leadership and "
            "client communication are essential. Familiarity with GDPR and data residency constraints a strong plus."
        ),
        "capabilities": [
            ("RAG Systems", 1.0, "critical"),
            ("LangChain", 0.9, "critical"),
            ("Azure AI Services", 0.8, "high"),
            ("Vector Databases", 0.8, "high"),
            ("Security & Compliance", 0.7, "high"),
            ("Technical Leadership", 0.7, "high"),
            ("Data Privacy & GDPR", 0.6, "high"),
            ("Python", 0.6, "medium"),
        ],
    },
    {
        "client_name": "HSBC",
        "raw_text": (
            "Looking for an MLOps engineer to productionise LLM pipelines in a highly regulated banking "
            "environment. Strong MLOps, CI/CD, Docker/Kubernetes, evaluation and benchmarking, and cost "
            "optimisation required. Python and Azure AI experience essential. Familiarity with model drift "
            "detection and automated retraining pipelines a strong plus."
        ),
        "capabilities": [
            ("MLOps", 1.0, "critical"),
            ("CI/CD Pipelines", 0.9, "critical"),
            ("Docker & Kubernetes", 0.9, "critical"),
            ("Evaluation & Benchmarking", 0.8, "high"),
            ("Cost Optimisation", 0.7, "high"),
            ("Azure AI Services", 0.7, "high"),
            ("Security & Compliance", 0.8, "high"),
            ("Experiment Tracking (MLflow/W&B)", 0.6, "medium"),
        ],
    },
    {
        "client_name": "NHS Digital",
        "raw_text": (
            "Building an agentic AI workflow for clinical decision support across GP and hospital settings. "
            "Requires deep expertise in agentic frameworks, prompt engineering, RAG, and knowledge of UK "
            "health data governance (IG, DSPT). Must have strong system design and Python skills. "
            "Experience with HL7 FHIR or NHS data standards is a strong advantage."
        ),
        "capabilities": [
            ("Agentic AI Frameworks", 1.0, "critical"),
            ("RAG Systems", 0.9, "critical"),
            ("Prompt Engineering", 0.9, "critical"),
            ("System Design", 0.8, "high"),
            ("Security & Compliance", 0.9, "critical"),
            ("Data Privacy & GDPR", 0.8, "high"),
            ("Python", 0.7, "high"),
            ("Embeddings & Retrieval", 0.7, "high"),
        ],
    },
    {
        "client_name": "Shell",
        "raw_text": (
            "Seeking a full-stack AI engineer to build an internal knowledge management platform with "
            "semantic search, embeddings, and a modern React/Next.js frontend for 10,000+ employees. "
            "Python backend with FastAPI, vector databases, and OpenAI API experience required. "
            "Experience with streaming responses and real-time UX for LLM outputs preferred."
        ),
        "capabilities": [
            ("Semantic Search", 1.0, "critical"),
            ("Embeddings & Retrieval", 0.9, "critical"),
            ("React / Next.js", 0.8, "high"),
            ("OpenAI API", 0.8, "high"),
            ("Vector Databases", 0.8, "high"),
            ("Python", 0.7, "high"),
            ("FastAPI", 0.6, "medium"),
            ("REST API Design", 0.5, "medium"),
        ],
    },
    {
        "client_name": "Deloitte",
        "raw_text": (
            "Need a principal AI architect to lead design of a multi-agent system for audit automation "
            "across financial statements and regulatory filings. Strong distributed systems, agentic AI, "
            "LLM fine-tuning, and technical leadership required. Client-facing role with partner exposure. "
            "Experience with AutoGen, CrewAI, or similar multi-agent frameworks highly desirable."
        ),
        "capabilities": [
            ("Distributed Systems", 1.0, "critical"),
            ("Agentic AI Frameworks", 1.0, "critical"),
            ("Multi-Agent Orchestration", 0.9, "critical"),
            ("System Design", 0.9, "critical"),
            ("Technical Leadership", 0.9, "critical"),
            ("Fine-tuning LLMs", 0.8, "high"),
            ("Client Communication", 0.8, "high"),
            ("AutoGen / CrewAI", 0.7, "high"),
            ("OpenAI API", 0.7, "high"),
        ],
    },
    {
        "client_name": "BP",
        "raw_text": (
            "AI data engineer needed to build ML data pipelines and feature stores for predictive "
            "maintenance models across offshore assets. Data engineering, Python, MLOps, and cloud "
            "(AWS Bedrock or Azure) experience required. Experience with streaming data from IoT sensors "
            "via Kafka or Kinesis is a strong plus."
        ),
        "capabilities": [
            ("Data Engineering", 1.0, "critical"),
            ("MLOps", 0.9, "critical"),
            ("Python", 0.8, "high"),
            ("AWS Bedrock", 0.7, "high"),
            ("Streaming Data (Kafka/Kinesis)", 0.8, "high"),
            ("Azure AI Services", 0.6, "medium"),
            ("CI/CD Pipelines", 0.7, "high"),
            ("Docker & Kubernetes", 0.6, "medium"),
        ],
    },
    {
        "client_name": "Barclays",
        "raw_text": (
            "Require an AI engineer with strong OpenAI API and Anthropic Claude integration experience "
            "to build conversational AI for retail banking customers. LLM guardrails, security, cost "
            "optimisation, evaluation, and Python are essential. Must have experience with A/B testing "
            "AI responses and continuous evaluation frameworks."
        ),
        "capabilities": [
            ("OpenAI API", 1.0, "critical"),
            ("Anthropic Claude API", 0.9, "critical"),
            ("Prompt Engineering", 0.8, "high"),
            ("LLM Guardrails & Safety", 0.9, "critical"),
            ("Security & Compliance", 0.9, "critical"),
            ("Cost Optimisation", 0.8, "high"),
            ("Evaluation & Benchmarking", 0.8, "high"),
            ("Python", 0.7, "high"),
        ],
    },
    {
        "client_name": "DVLA",
        "raw_text": (
            "Government digital transformation: AI engineer to build document processing and information "
            "extraction using Hugging Face models on Azure. MLOps, Docker, CI/CD, and SC security clearance "
            "required. Must be comfortable working within GDS standards and public sector procurement frameworks."
        ),
        "capabilities": [
            ("Hugging Face", 1.0, "critical"),
            ("Azure AI Services", 0.9, "critical"),
            ("MLOps", 0.8, "high"),
            ("Docker & Kubernetes", 0.8, "high"),
            ("CI/CD Pipelines", 0.7, "high"),
            ("Security & Compliance", 0.9, "critical"),
            ("Data Engineering", 0.6, "medium"),
            ("Model Quantisation", 0.5, "medium"),
        ],
    },
    {
        "client_name": "Vodafone",
        "raw_text": (
            "Looking for a Google Vertex AI specialist to build LLM-powered customer experience analytics "
            "across 15 European markets. GCP expertise, Vertex AI, LlamaIndex, vector databases, and Python "
            "required. Scalability, distributed systems, and multilingual NLP experience are a strong plus."
        ),
        "capabilities": [
            ("Google Vertex AI", 1.0, "critical"),
            ("LlamaIndex", 0.9, "critical"),
            ("Vector Databases", 0.8, "high"),
            ("Python", 0.8, "high"),
            ("Distributed Systems", 0.7, "medium"),
            ("Embeddings & Retrieval", 0.8, "high"),
            ("Evaluation & Benchmarking", 0.6, "medium"),
            ("Observability & Monitoring", 0.6, "medium"),
        ],
    },
    {
        "client_name": "Lloyd's of London",
        "raw_text": (
            "Senior AI engineer for insurance document intelligence across specialty lines and reinsurance. "
            "RAG, LlamaIndex, OpenAI, vector stores, FastAPI backend, and TypeScript frontend. Knowledge "
            "graph integration for policy and claims data is a differentiator. Domain knowledge in insurance "
            "or Lloyd's market operations is a significant advantage."
        ),
        "capabilities": [
            ("RAG Systems", 1.0, "critical"),
            ("LlamaIndex", 0.9, "critical"),
            ("OpenAI API", 0.8, "high"),
            ("Vector Databases", 0.8, "high"),
            ("Knowledge Graph Integration", 0.7, "high"),
            ("FastAPI", 0.7, "high"),
            ("TypeScript / Node.js", 0.7, "high"),
            ("Embeddings & Retrieval", 0.7, "high"),
        ],
    },
    {
        "client_name": "BT Group",
        "raw_text": (
            "AI platform engineer to build internal developer tooling powered by LLMs. Need strong "
            "experience in agentic frameworks, tool use and function calling, REST API design, and "
            "TypeScript/Node.js. Must be able to build robust evals and observability layers for "
            "production LLM systems serving thousands of internal developers daily."
        ),
        "capabilities": [
            ("Tool Use & Function Calling", 1.0, "critical"),
            ("Agentic AI Frameworks", 0.9, "critical"),
            ("REST API Design", 0.8, "high"),
            ("TypeScript / Node.js", 0.8, "high"),
            ("Observability & Monitoring", 0.8, "high"),
            ("Evaluation & Benchmarking", 0.7, "high"),
            ("Docker & Kubernetes", 0.6, "medium"),
            ("Python", 0.7, "high"),
        ],
    },
    {
        "client_name": "Rolls-Royce",
        "raw_text": (
            "Senior ML engineer to build AI-assisted engineering design tools for aerospace applications. "
            "Strong Python, MLOps, experiment tracking (MLflow/W&B), and distributed training required. "
            "Experience with simulation data, physics-informed ML, or digital twin architectures is "
            "highly desirable. SC clearance required or willingness to undergo clearance."
        ),
        "capabilities": [
            ("MLOps", 1.0, "critical"),
            ("Experiment Tracking (MLflow/W&B)", 0.9, "critical"),
            ("Distributed Systems", 0.8, "high"),
            ("Python", 0.9, "critical"),
            ("Fine-tuning LLMs", 0.6, "medium"),
            ("Security & Compliance", 0.8, "high"),
            ("Docker & Kubernetes", 0.7, "high"),
            ("AWS SageMaker", 0.6, "medium"),
        ],
    },
    {
        "client_name": "Sainsbury's",
        "raw_text": (
            "AI engineer to build personalisation and recommendation systems using LLMs and embedding "
            "models at retail scale. Experience with AWS Bedrock, semantic search, PostgreSQL/pgvector, "
            "and real-time recommendation pipelines essential. Agile delivery and stakeholder management "
            "skills important as you'll work directly with commercial and trading teams."
        ),
        "capabilities": [
            ("AWS Bedrock", 1.0, "critical"),
            ("Semantic Search", 0.9, "critical"),
            ("PostgreSQL / pgvector", 0.9, "critical"),
            ("Embeddings & Retrieval", 0.8, "high"),
            ("Streaming Data (Kafka/Kinesis)", 0.7, "high"),
            ("Agile Delivery", 0.7, "high"),
            ("Stakeholder Management", 0.6, "medium"),
            ("Python", 0.8, "high"),
        ],
    },
    {
        "client_name": "Prudential",
        "raw_text": (
            "Looking for a principal AI engineer to lead an APAC-wide AI transformation for life insurance "
            "underwriting. Strong RAG, agentic AI, Azure OpenAI, and multi-agent orchestration. Must have "
            "senior stakeholder management experience and the ability to run delivery across Singapore, "
            "Hong Kong, and Malaysia. Experience in insurance or actuarial domains is a material advantage."
        ),
        "capabilities": [
            ("RAG Systems", 1.0, "critical"),
            ("Multi-Agent Orchestration", 0.9, "critical"),
            ("Azure OpenAI Service", 0.9, "critical"),
            ("Agentic AI Frameworks", 0.8, "high"),
            ("Technical Leadership", 0.9, "critical"),
            ("Stakeholder Management", 0.9, "critical"),
            ("Security & Compliance", 0.7, "high"),
            ("Client Communication", 0.8, "high"),
        ],
    },
    {
        "client_name": "Network Rail",
        "raw_text": (
            "AI engineer to build computer vision and NLP solutions for infrastructure inspection and "
            "maintenance planning. Hugging Face model fine-tuning, MLOps, Azure AI, and Docker required. "
            "Must have experience deploying models to edge devices or constrained compute environments. "
            "SC clearance required."
        ),
        "capabilities": [
            ("Hugging Face", 1.0, "critical"),
            ("Fine-tuning LLMs", 0.9, "critical"),
            ("MLOps", 0.8, "high"),
            ("Azure AI Services", 0.8, "high"),
            ("Model Quantisation", 0.8, "high"),
            ("Docker & Kubernetes", 0.7, "high"),
            ("Security & Compliance", 0.8, "high"),
            ("Evaluation & Benchmarking", 0.6, "medium"),
        ],
    },
    {
        "client_name": "Clifford Chance",
        "raw_text": (
            "Legal AI engineer to build document review, contract analysis, and legal research tools "
            "using LLMs. Strong RAG, LangChain, prompt engineering, and vector database experience. "
            "Must understand legal privilege, data confidentiality, and zero-trust data handling. "
            "Prior experience in legal tech or professional services AI is highly valued."
        ),
        "capabilities": [
            ("RAG Systems", 1.0, "critical"),
            ("LangChain", 0.9, "critical"),
            ("Prompt Engineering", 0.9, "critical"),
            ("Vector Databases", 0.8, "high"),
            ("LLM Guardrails & Safety", 0.8, "high"),
            ("Zero Trust Architecture", 0.8, "high"),
            ("Data Privacy & GDPR", 0.9, "critical"),
            ("Security & Compliance", 0.8, "high"),
        ],
    },
    {
        "client_name": "GSK",
        "raw_text": (
            "Senior AI scientist to accelerate drug discovery workflows using LLMs and knowledge graphs. "
            "Experience with biomedical NLP, Hugging Face, knowledge graph integration, and Python essential. "
            "Familiarity with clinical trial data, PubMed, or ChEMBL datasets is a strong differentiator. "
            "MLOps and experiment tracking required for reproducible research workflows."
        ),
        "capabilities": [
            ("Knowledge Graph Integration", 1.0, "critical"),
            ("Hugging Face", 0.9, "critical"),
            ("Embeddings & Retrieval", 0.8, "high"),
            ("RAG Systems", 0.8, "high"),
            ("Experiment Tracking (MLflow/W&B)", 0.8, "high"),
            ("MLOps", 0.7, "high"),
            ("Python", 0.9, "critical"),
            ("Fine-tuning LLMs", 0.7, "high"),
        ],
    },
    {
        "client_name": "Cazoo",
        "raw_text": (
            "AI engineer to build LLM-powered vehicle listing optimisation, chatbot, and search ranking "
            "systems. OpenAI API, semantic search, PostgreSQL/pgvector, and Python backend required. "
            "Strong React/Next.js for AI-powered frontend features. Agile delivery experience in a "
            "fast-paced product environment is essential."
        ),
        "capabilities": [
            ("OpenAI API", 1.0, "critical"),
            ("Semantic Search", 0.9, "critical"),
            ("PostgreSQL / pgvector", 0.8, "high"),
            ("React / Next.js", 0.8, "high"),
            ("Prompt Engineering", 0.7, "high"),
            ("Python", 0.8, "high"),
            ("FastAPI", 0.6, "medium"),
            ("Agile Delivery", 0.7, "high"),
        ],
    },
    {
        "client_name": "EY",
        "raw_text": (
            "AI delivery lead for a tax and audit AI transformation programme. Must combine strong "
            "technical depth in agentic AI and RAG with the ability to lead cross-functional delivery "
            "teams and manage partner-level relationships. Experience in IaC, Terraform, and enterprise "
            "cloud governance required. Prior Big Four or professional services experience strongly preferred."
        ),
        "capabilities": [
            ("Agentic AI Frameworks", 1.0, "critical"),
            ("RAG Systems", 0.9, "critical"),
            ("Technical Leadership", 1.0, "critical"),
            ("Stakeholder Management", 0.9, "critical"),
            ("Client Communication", 0.9, "critical"),
            ("Terraform / IaC", 0.7, "high"),
            ("Security & Compliance", 0.8, "high"),
            ("Agile Delivery", 0.8, "high"),
        ],
    },
    {
        "client_name": "Monzo",
        "raw_text": (
            "AI product engineer to build next-generation AI features across Monzo's consumer banking app. "
            "Strong prompt engineering, OpenAI and Anthropic API experience, TypeScript/Node.js, and React "
            "required. You'll own end-to-end AI feature delivery from ideation to production, with a focus "
            "on responsible AI, cost control, and exceptional user experience."
        ),
        "capabilities": [
            ("Prompt Engineering", 1.0, "critical"),
            ("OpenAI API", 0.9, "critical"),
            ("Anthropic Claude API", 0.8, "high"),
            ("TypeScript / Node.js", 0.9, "critical"),
            ("React / Next.js", 0.8, "high"),
            ("LLM Guardrails & Safety", 0.8, "high"),
            ("Cost Optimisation", 0.8, "high"),
            ("Evaluation & Benchmarking", 0.7, "high"),
        ],
    },
]

ENGINEER_NAMES = [
    # Original 30
    "Aisha Patel", "Marcus Chen", "Priya Sharma", "James O'Brien", "Fatima Al-Hassan",
    "Tom Eriksson", "Mei Lin", "Daniel Okonkwo", "Sophie Laurent", "Raj Kapoor",
    "Elena Volkov", "Carlos Mendez", "Zara Ahmed", "Luke Fitzgerald", "Yuki Tanaka",
    "Nadia Kowalski", "Ibrahim Al-Farsi", "Charlotte Webb", "Kwame Asante", "Anna Lindqvist",
    "Mohammed Al-Rashid", "Grace Osei", "Ben Harrison", "Layla Nasser", "Stefan Muller",
    "Chioma Obi", "David Kim", "Isabelle Dupont", "Tariq Hussain", "Rosa Martinez",
    # Additional 30
    "Oliver Blackwood", "Amara Diallo", "Ethan Johansson", "Lena Fischer", "Kwabena Mensah",
    "Sakura Watanabe", "Ravi Krishnamurthy", "Aoife Murphy", "Mateus Costa", "Ingrid Haugen",
    "Caleb Oduya", "Hana Nakamura", "Pedro Alves", "Miriam Goldstein", "Ade Adeyemi",
    "Freya Andersen", "Siddharth Iyer", "Chloe Beaumont", "Emeka Nwosu", "Luca Ferretti",
    "Amelia Thornton", "Yusuf Ibrahim", "Clara Hoffman", "Nikhil Mehta", "Blessing Eze",
    "Rafael Monteiro", "Siobhan Kelly", "Arjun Nair", "Valentina Romano", "Kofi Asare",
]

BIOS = [
    "Specialist in production RAG systems and enterprise knowledge retrieval at scale.",
    "MLOps engineer with a track record of shipping LLM pipelines in regulated financial services.",
    "Full-stack AI engineer focused on developer tooling and agentic workflow automation.",
    "Cloud AI architect with deep expertise across AWS Bedrock, Azure OpenAI, and GCP Vertex.",
    "Prompt engineering specialist and LLM evaluation framework builder.",
    "Data infrastructure engineer with extensive experience in vector databases and semantic search.",
    "Multi-agent systems designer with a background in distributed systems and microservices.",
    "AI security and compliance specialist working primarily in banking and government sectors.",
    "Fine-tuning and RLHF practitioner with Hugging Face and custom training infrastructure experience.",
    "Technical lead and delivery manager for large-scale AI transformation programmes.",
    "RAG and knowledge graph engineer with domain expertise in legal and professional services AI.",
    "Cost optimisation and model efficiency specialist focused on LLM inference at enterprise scale.",
    "AI product engineer building consumer-facing LLM features with a focus on UX and safety.",
    "Agentic AI researcher and practitioner building autonomous workflows for enterprise clients.",
    "ML platform engineer with experience in experiment tracking, feature stores, and model registries.",
]

CERTIFICATIONS = [
    ("Azure AI Engineer Associate", "Microsoft"),
    ("AWS ML Specialty", "Amazon"),
    ("GCP Professional ML Engineer", "Google"),
    ("Azure OpenAI Fundamentals", "Microsoft"),
    ("AWS Certified Solutions Architect", "Amazon"),
    ("Certified Kubernetes Administrator", "CNCF"),
    ("HashiCorp Terraform Associate", "HashiCorp"),
    ("Databricks Certified Associate Developer", "Databricks"),
    ("Hugging Face NLP Course Certificate", "Hugging Face"),
    ("DeepLearning.AI MLOps Specialisation", "Coursera"),
]

PROJECT_DESCRIPTIONS = [
    "Built a production RAG pipeline for legal document review, reducing analyst review time by 60%.",
    "Deployed multi-agent agentic workflow for automated financial audit across 12 regulatory frameworks.",
    "Designed and shipped semantic search platform serving 50,000 daily active users at a FTSE 100 retailer.",
    "Led MLOps infrastructure migration to Kubernetes, cutting model deployment time from 2 weeks to 2 hours.",
    "Fine-tuned domain-specific LLM on proprietary insurance data, achieving 23% accuracy improvement over GPT-4.",
    "Built real-time LLM observability platform tracking cost, latency, and quality across 15 production models.",
    "Delivered conversational AI for retail banking serving 2M+ customers, with guardrails and safety layers.",
    "Architected knowledge graph integration for pharmaceutical research, connecting 4M+ biomedical entities.",
    "Shipped LLM-powered developer copilot used by 800 internal engineers at a UK telecoms company.",
    "Built streaming data pipeline processing 500K IoT sensor events per second for predictive maintenance AI.",
    "Designed zero-trust LLM deployment for government client with SC clearance and air-gapped inference.",
    "Implemented RLHF preference data pipeline and fine-tuning workflow for a customer support LLM.",
    "Built multi-lingual embedding and retrieval system supporting 14 European languages for global enterprise.",
    "Delivered Azure OpenAI integration for clinical decision support tool used across 40 NHS trusts.",
    "Designed cost optimisation framework saving £800K/year in LLM inference costs for a global bank.",
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # 1. Create skills
        skill_objs = {}
        for name, category in SKILLS:
            res = await db.execute(select(Skill).where(Skill.name == name))
            sk = res.scalar_one_or_none()
            if not sk:
                sk = Skill(name=name, category=category)
                db.add(sk)
            skill_objs[name] = sk
        await db.flush()

        # 2. Create admin + leadership + named engineer accounts
        for role, email, name, seniority in [
            ("leadership", "leadership@nexus.ai", "Leadership User", "principal"),
            ("admin", "admin@nexus.ai", "Admin User", "principal"),
            ("engineer", "rihan@nexus.ai", "Rihan Yakoob", "principal"),
            ("engineer", "aisha.patel@nexus.ai", "Aisha Patel", "senior"),
            ("engineer", "marcus.chen@nexus.ai", "Marcus Chen", "senior"),
        ]:
            res = await db.execute(select(Engineer).where(Engineer.email == email))
            if not res.scalar_one_or_none():
                eng = Engineer(
                    name=name,
                    email=email,
                    hashed_password=hash_password("nexus123"),
                    role=role,
                    seniority=seniority,
                    bio=random.choice(BIOS),
                )
                db.add(eng)
        await db.flush()

        # 3. Create 60 engineers with realistic distributions
        created_engineers = []
        for i, name in enumerate(ENGINEER_NAMES):
            cleaned_name = name.lower().replace(" ", ".").replace("'", "")
            email = f"{cleaned_name}@nexus.ai"
            res = await db.execute(select(Engineer).where(Engineer.email == email))
            if res.scalar_one_or_none():
                continue

            seniority = random.choices(SENIORITIES, weights=SENIORITY_WEIGHTS, k=1)[0]

            # Senior/principal engineers get more skills
            skill_count_map = {
                "junior": (3, 6),
                "mid": (5, 9),
                "senior": (7, 12),
                "principal": (10, 15),
            }
            min_skills, max_skills = skill_count_map[seniority]

            eng = Engineer(
                name=name,
                email=email,
                hashed_password=hash_password("nexus123"),
                role="engineer",
                seniority=seniority,
                bio=random.choice(BIOS),
            )
            db.add(eng)
            await db.flush()
            created_engineers.append(eng)

            # Assign skills with realistic source distribution by seniority
            skill_subset = random.sample(list(skill_objs.values()), k=random.randint(min_skills, max_skills))
            for sk in skill_subset:
                # More senior engineers have more proven/demonstrated evidence
                if seniority == "principal":
                    source = random.choices(["claimed", "demonstrated", "proven"], weights=[0.1, 0.3, 0.6])[0]
                elif seniority == "senior":
                    source = random.choices(["claimed", "demonstrated", "proven"], weights=[0.2, 0.4, 0.4])[0]
                elif seniority == "mid":
                    source = random.choices(["claimed", "demonstrated", "proven"], weights=[0.4, 0.4, 0.2])[0]
                else:
                    source = random.choices(["claimed", "demonstrated", "proven"], weights=[0.7, 0.25, 0.05])[0]

                # Score range varies by seniority
                score_ranges = {
                    "principal": (7.0, 10.0),
                    "senior": (6.0, 9.5),
                    "mid": (4.5, 8.0),
                    "junior": (3.0, 6.5),
                }
                lo, hi = score_ranges[seniority]
                score = round(random.uniform(lo, hi), 1)

                es = EngineerSkill(
                    engineer_id=eng.id,
                    skill_id=sk.id,
                    claimed_score=score,
                    source=source,
                    last_updated=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365)),
                )
                ev_list = []
                if source in ("demonstrated", "proven"):
                    ev_count = 2 if source == "proven" else 1
                    for _ in range(ev_count):
                        ev = Evidence(
                            engineer_id=eng.id,
                            skill_id=sk.id,
                            type=random.choice(["project", "client_delivery", "assessment", "peer_review"]),
                            description=random.choice(PROJECT_DESCRIPTIONS),
                            date=datetime.now(timezone.utc) - timedelta(days=random.randint(10, 730)),
                        )
                        db.add(ev)
                        ev_list.append(ev)
                es.confidence_score = compute_confidence(score, source, ev_list)
                db.add(es)

            # Certifications: more certs for senior engineers
            cert_count_map = {"junior": (0, 1), "mid": (0, 2), "senior": (1, 3), "principal": (2, 4)}
            min_certs, max_certs = cert_count_map[seniority]
            cert_sample = random.sample(CERTIFICATIONS, k=random.randint(min_certs, max_certs))
            for cert_name, issuer in cert_sample:
                issued = datetime.now(timezone.utc) - timedelta(days=random.randint(30, 900))
                cert = Certification(
                    engineer_id=eng.id,
                    name=cert_name,
                    issuer=issuer,
                    date=issued,
                    expiry=issued + timedelta(days=random.randint(365, 1095)),
                )
                db.add(cert)

        await db.flush()

        # 4. Create JDs
        for jd_data in JD_TEMPLATES:
            res = await db.execute(select(JD).where(JD.client_name == jd_data["client_name"]))
            existing_jd = res.scalar_one_or_none()
            if existing_jd:
                existing_jd.status = "published"
                existing_jd.is_published = True
                continue
            jd = JD(
                client_name=jd_data["client_name"],
                raw_text=jd_data["raw_text"],
                capability_blueprint={
                    "seeded": True,
                    "summary": jd_data["raw_text"][:120],
                    "capability_count": len(jd_data["capabilities"]),
                },
                status="published",
                is_published=True,
            )
            db.add(jd)
            await db.flush()

            for skill_name, weight, priority in jd_data["capabilities"]:
                sk = skill_objs.get(skill_name)
                if sk:
                    cap = JDCapability(jd_id=jd.id, skill_id=sk.id, weight=weight, priority=priority)
                    db.add(cap)

        await db.commit()
        print("✅ Seed complete.")
        print(f"   Engineers: {len(ENGINEER_NAMES)} synthetic + 3 named accounts")
        print(f"   JDs: {len(JD_TEMPLATES)} client job descriptions")
        print(f"   Skills: {len(SKILLS)} across 8 categories")
        print()
        print("   Login accounts:")
        print("   admin@nexus.ai / nexus123")
        print("   leadership@nexus.ai / nexus123")
        print("   rihan@nexus.ai / nexus123")


if __name__ == "__main__":
    asyncio.run(seed())