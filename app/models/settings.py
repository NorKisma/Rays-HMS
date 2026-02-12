from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin


class SystemSetting(db.Model, SoftDeleteMixin, TimestampMixin):
    """
    Simple key/value settings store for system configuration.

    Examples of keys:
    - 'billing.service.Consultation.price'
    - 'billing.service.Computer Service.price'
    - 'billing.card_fee'
    """

    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(150), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    group = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<SystemSetting {self.key}={self.value}>"

    @staticmethod
    def get(key: str, default=None):
        """
        Fetch a setting by key.
        Returns the stored string value, or default if missing.
        """
        setting = SystemSetting.query.filter_by(key=key, is_deleted=False).first()
        if setting is None:
            return default
        return setting.value

    @staticmethod
    def set(key: str, value, group: str | None = None, description: str | None = None):
        """
        Create or update a setting.
        Value is stored as string; caller is responsible for casting.
        """
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting is None:
            setting = SystemSetting(key=key)

        setting.value = str(value)
        if group is not None:
            setting.group = group
        if description is not None:
            setting.description = description

        db.session.add(setting)
        return setting

