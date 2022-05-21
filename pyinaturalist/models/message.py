from typing import List

from pyinaturalist.constants import DATETIME_SHORT_FORMAT, DateTime, TableRow
from pyinaturalist.models import BaseModel, LazyProperty, User, datetime_field, define_model, field


@define_model
class Message(BaseModel):
    """:fa:`user` A message from the user's inbox, based on the schema of
    :v1:`GET /messages <Messages/get_messages>`
    """

    user_id: int = field(default=None, doc='Corresponding user ID')
    thread_id: int = field(default=None, doc='Message thread ID')
    subject: str = field(default=None, doc='Message subject')
    body: str = field(default=None, doc='Message body')
    read_at: DateTime = datetime_field(doc='When the message was read')
    created_at: DateTime = datetime_field(doc='When the message was sent')
    updated_at: DateTime = datetime_field(doc='When the message was last edited')
    thread_flags: List[str] = field(factory=list)
    thread_messages_count: int = field(default=None, doc='Number of messages in the thread')

    from_user: property = LazyProperty(User.from_json, type=User, doc='Message sender')
    to_user: property = LazyProperty(User.from_json, type=User, doc='Message recipient')

    @property
    def truncated_body(self):
        """Comment text, truncated"""
        truncated_body = self.body.replace('\n', ' ').strip()
        if len(truncated_body) > 50:
            truncated_body = truncated_body[:47].strip() + '...'
        return truncated_body

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Date': self.created_at,
            'To': self.to_user.login,
            'From': self.from_user.login,
            'Subject': self.subject,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'created_at', 'self.to_user', 'self.from_user', 'subject', 'truncated_body']

    def __str__(self) -> str:
        return (
            f'[{self.id}] Sent {self.created_at.strftime(DATETIME_SHORT_FORMAT)} '
            f'from {self.from_user.login} to {self.to_user.login}: {self.subject}'
        )
