import yaml
from src.models.startup_profile import StartupProfile, CustomerType, FieldWithSource, InfoSource

class InputParserAgent:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        with open('config/prompts.yaml', 'r') as f:
            self.prompts = yaml.safe_load(f)

    async def parse(self, problem_statement: str) -> StartupProfile:
        system_instruction = self.prompts.get('input_parsing', '')
        
        try:
            return await self.llm_client.generate_structured(problem_statement, system_instruction, StartupProfile)
        except Exception as e:
            print(f"LLM input parsing note: {e}, using heuristic extraction fallback.")
            text = problem_statement.lower()
            
            # Heuristic vertical detection
            if any(k in text for k in ["health", "hospital", "patient", "medical", "clinic", "clinical", "doctor", "drug"]):
                ind = "Healthcare Technology"
                sub_ind = "Clinical AI & Hospital Operations"
                cust = "Hospitals, Health Systems, and Care Providers"
                cust_type = CustomerType.B2B
                tech = "Artificial Intelligence & Predictive Analytics"
                reg = "HIPAA, FDA Software as a Medical Device (SaMD)"
            elif any(k in text for k in ["fintech", "payment", "bank", "credit", "lending", "crypto", "fraud", "wallet"]):
                ind = "FinTech"
                sub_ind = "Payments & Financial Infrastructure"
                cust = "Financial Institutions & Businesses"
                cust_type = CustomerType.B2B
                tech = "API-driven Financial Infrastructure"
                reg = "SEC, CFPB, FinCEN compliance"
            elif any(k in text for k in ["consumer", "social", "app", "creators", "video", "media"]):
                ind = "Consumer Social"
                sub_ind = "Digital Media & Community"
                cust = "End Consumers & Digital Creators"
                cust_type = CustomerType.B2C
                tech = "Mobile and Web Application"
                reg = "GDPR, COPPA, Data Privacy"
            else:
                ind = "B2B SaaS"
                sub_ind = "Enterprise Productivity & Automation"
                cust = "Enterprise Business Customers"
                cust_type = CustomerType.B2B
                tech = "Cloud-native Software Platform"
                reg = "SOC2, ISO 27001, Enterprise Security"

            from src.models.startup_profile import FieldWithSource, InfoSource
            return StartupProfile(
                industry=FieldWithSource(value=ind, source=InfoSource.INFERRED),
                sub_industry=FieldWithSource(value=sub_ind, source=InfoSource.INFERRED),
                target_customers=FieldWithSource(value=cust, source=InfoSource.INFERRED),
                customer_type=FieldWithSource(value=cust_type, source=InfoSource.INFERRED),
                problem_description=FieldWithSource(value=problem_statement, source=InfoSource.EXTRACTED),
                solution_description=FieldWithSource(value=f"Automated solution addressing: {problem_statement}", source=InfoSource.INFERRED),
                technology=FieldWithSource(value=tech, source=InfoSource.INFERRED),
                business_model=FieldWithSource(value="B2B Subscription / Recurring Enterprise Licensing", source=InfoSource.INFERRED),
                revenue_model=FieldWithSource(value="Annual Recurring Revenue (ARR)", source=InfoSource.INFERRED),
                geographic_market=FieldWithSource(value="North America / Global", source=InfoSource.INFERRED),
                regulatory_environment=FieldWithSource(value=reg, source=InfoSource.INFERRED),
                capital_requirements=FieldWithSource(value="Moderate to High Capital Intensity", source=InfoSource.INFERRED),
                operational_complexity=FieldWithSource(value="High Integration & Implementation Complexity", source=InfoSource.INFERRED),
                severity_of_problem=FieldWithSource(value="High Severity / Critical Workflow", source=InfoSource.INFERRED)
            )
