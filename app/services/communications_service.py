from datetime import datetime, timedelta

from app.database.models import (
    CommunicationAction,
    Conversation,
    ConversationMessage,
    ConversationParticipant,
    Employee,
    EmployeeMessage,
    EmployeeMemory,
    Vendor,
    VendorEvent,
)


class CommunicationsService:
    """Central nervous system for Atlas Enterprise communications.

    v2.5 keeps this local and deterministic. Later this service becomes the
    integration point for Gmail, Calendar, vendor portals, and customer support.
    """

    def __init__(self, session):
        self.session = session

    def ensure_seed_conversations(self) -> dict[str, int]:
        created = 0
        created += self._ensure_internal_launch_thread()
        created += self._ensure_vendor_rfq_thread()
        created += self._ensure_customer_support_thread()
        self.session.commit()
        return {
            "conversations_created": created,
            "open_conversations": self.session.query(Conversation).filter_by(status="open").count(),
            "open_actions": self.session.query(CommunicationAction).filter_by(status="open").count(),
        }

    def create_conversation(
        self,
        subject: str,
        conversation_type: str = "internal",
        context_type: str = "company",
        context_name: str = "Atlas Enterprise",
        participants: list[tuple[str, str, str]] | None = None,
        summary: str = "",
        priority: int = 5,
    ) -> Conversation:
        existing = self.session.query(Conversation).filter_by(subject=subject, context_name=context_name).first()
        if existing:
            return existing

        conversation = Conversation(
            subject=subject,
            conversation_type=conversation_type,
            context_type=context_type,
            context_name=context_name,
            priority=priority,
            summary=summary,
            status="open",
        )
        self.session.add(conversation)
        self.session.flush()

        for participant_type, display_name, role in participants or []:
            self.session.add(
                ConversationParticipant(
                    conversation_id=conversation.id,
                    participant_type=participant_type,
                    display_name=display_name,
                    role=role,
                )
            )
        self.session.flush()
        return conversation

    def add_message(
        self,
        conversation: Conversation,
        sender_name: str,
        body: str,
        message_type: str = "note",
        requires_response: bool = False,
    ) -> ConversationMessage:
        message = ConversationMessage(
            conversation_id=conversation.id,
            sender_name=sender_name,
            message_type=message_type,
            body=body,
            requires_response=requires_response,
        )
        conversation.updated_at = datetime.utcnow()
        self.session.add(message)
        self.session.flush()
        return message

    def create_action(
        self,
        conversation: Conversation,
        title: str,
        owner_name: str = "Mia Stone",
        action_type: str = "follow_up",
        days_until_due: int = 2,
    ) -> CommunicationAction:
        existing = self.session.query(CommunicationAction).filter_by(conversation_id=conversation.id, title=title).first()
        if existing:
            return existing
        action = CommunicationAction(
            conversation_id=conversation.id,
            owner_name=owner_name,
            action_type=action_type,
            title=title,
            status="open",
            due_at=datetime.utcnow() + timedelta(days=days_until_due),
        )
        self.session.add(action)
        self.session.flush()
        return action

    def complete_action(self, action_id: int) -> None:
        action = self.session.query(CommunicationAction).filter_by(id=action_id).first()
        if action:
            action.status = "complete"
            self.session.commit()

    def draft_vendor_rfq(self, vendor_id: int | None = None) -> str:
        vendor = self.session.query(Vendor).filter_by(id=vendor_id).first() if vendor_id else None
        vendor_name = vendor.name if vendor else "Vendor"
        capabilities = vendor.capabilities if vendor else "wood, acrylic, magnets, printing"
        return (
            f"Subject: RFQ Request for Youth Baseball Coaching Product Line\n\n"
            f"Hello {vendor_name},\n\n"
            f"We are evaluating production partners for a youth baseball coaching product line. "
            f"Please provide pricing, MOQ, lead time, customization options, packaging options, and sample availability.\n\n"
            f"Relevant capabilities we are looking for: {capabilities}.\n\n"
            f"Please include unit cost at 25, 100, and 250 units, estimated shipping, and production timeline.\n\n"
            f"Thank you,\nDavid Miller\nManufacturing Director, Atlas Enterprise"
        )

    def mark_conversation_waiting(self, conversation_id: int) -> None:
        conversation = self.session.query(Conversation).filter_by(id=conversation_id).first()
        if conversation:
            conversation.status = "waiting"
            conversation.updated_at = datetime.utcnow()
            self.session.commit()

    def _ensure_internal_launch_thread(self) -> int:
        conv = self.create_conversation(
            subject="Diamond Edge launch coordination",
            conversation_type="internal",
            context_type="business",
            context_name="Diamond Edge",
            summary="Sarah is coordinating manufacturing, finance, and marketing inputs before recommending launch.",
            priority=8,
            participants=[
                ("employee", "Sarah Williams", "owner"),
                ("employee", "David Miller", "manufacturing"),
                ("employee", "Michael Grant", "finance"),
                ("employee", "Emma Rivera", "marketing"),
            ],
        )
        if self.session.query(ConversationMessage).filter_by(conversation_id=conv.id).count() == 0:
            self.add_message(conv, "Sarah Williams", "Please confirm manufacturing assumptions and finance guardrails before launch.", requires_response=True)
            self.add_message(conv, "David Miller", "I am comparing preferred vendors against MOQ, landed cost, and lead time.")
            self.add_message(conv, "Michael Grant", "I need landed cost before approving target price and margin.")
            self.create_action(conv, "Michael to approve margin once landed cost is confirmed", owner_name="Michael Grant", action_type="finance_review", days_until_due=1)
            return 1
        return 0

    def _ensure_vendor_rfq_thread(self) -> int:
        vendor = self.session.query(Vendor).order_by(Vendor.trust_score.desc()).first()
        vendor_name = vendor.name if vendor else "Preferred Vendor"
        conv = self.create_conversation(
            subject=f"RFQ with {vendor_name}",
            conversation_type="vendor",
            context_type="vendor",
            context_name=vendor_name,
            summary="David is preparing an RFQ and Mia is tracking follow-up so vendor pricing can update Finance.",
            priority=9,
            participants=[
                ("employee", "David Miller", "owner"),
                ("employee", "Mia Stone", "follow-up"),
                ("vendor", vendor_name, "supplier"),
            ],
        )
        if self.session.query(ConversationMessage).filter_by(conversation_id=conv.id).count() == 0:
            self.add_message(conv, "David Miller", "Drafting RFQ for lineup boards, dugout signs, and team banners.")
            self.add_message(conv, vendor_name, "Please send dimensions, artwork format, and target order quantities so we can quote accurately.", message_type="vendor_reply", requires_response=True)
            self.create_action(conv, "Send RFQ package and request tiered pricing", owner_name="Mia Stone", action_type="rfq_follow_up", days_until_due=1)
            if vendor:
                self.session.add(VendorEvent(vendor_id=vendor.id, event_type="rfq_thread_created", actor="Mia Stone", message="Communications Hub created RFQ tracking conversation."))
            return 1
        return 0

    def _ensure_customer_support_thread(self) -> int:
        conv = self.create_conversation(
            subject="Customer support policy draft",
            conversation_type="customer",
            context_type="policy",
            context_name="Youth Baseball Coaching Products",
            summary="Olivia is preparing customer response policies for customization, shipping expectations, and returns.",
            priority=6,
            participants=[
                ("employee", "Olivia Parker", "owner"),
                ("employee", "Emma Rivera", "brand voice"),
                ("employee", "Mia Stone", "routing"),
            ],
        )
        if self.session.query(ConversationMessage).filter_by(conversation_id=conv.id).count() == 0:
            self.add_message(conv, "Olivia Parker", "Drafting support macros for logo uploads, personalization revisions, and shipping questions.")
            self.add_message(conv, "Emma Rivera", "Keep the tone coach-friendly, premium, and reassuring.")
            self.create_action(conv, "Create support macros for customization questions", owner_name="Olivia Parker", action_type="support_macro", days_until_due=3)
            return 1
        return 0
