import sys
from pathlib import Path
from datetime import datetime

# Add root to path
sys.path.insert(0, str(Path.cwd()))
from jarvis.db.database import Database
from jarvis.skills.profile import ProfileService

db = Database(Path("data/jarvis.db"))
profile_svc = ProfileService(db)

# Set grad date to something in the future, e.g., 49 days from now as mentioned in quotes
from datetime import timedelta
import datetime

profile = profile_svc.get_profile()
new_grad_date = datetime.date.today() + timedelta(days=49)
profile_svc.update_profile(grad_deadline=new_grad_date, graduation_date=new_grad_date)
print(f"Updated graduation date to: {new_grad_date}")
