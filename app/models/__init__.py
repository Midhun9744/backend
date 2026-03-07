# Import all models so SQLAlchemy can register them

from .user import User
from .household import Household
from .monitored_person import MonitoredPerson
from .access_permission import AccessPermission
from .device import Device
from .activity import Activity
from .alert import Alert
from .alert_recipient import AlertRecipient
