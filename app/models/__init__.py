# Import every table model here so SQLModel.metadata knows about all of them
# when init_db() runs create_all(). If you add a new model file, import it here too.
from app.models.voter import Voter
from app.models.roster import ApprovedRoster
from app.models.portfolio import Portfolio
from app.models.candidate import Candidate
from app.models.vote import Vote
from app.models.election_settings import ElectionSettings
