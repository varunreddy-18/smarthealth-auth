from app.database.database import Base, engine

# Import all models
from app.models import User

Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully!")