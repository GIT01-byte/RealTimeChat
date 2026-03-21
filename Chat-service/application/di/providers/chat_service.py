from dishka import Provider, Scope, provide

from application.core.chats.use_cases.send_message import SendMessageUseCase
from application.repositories.chat_messages_repo import ChatMessagesRepo
from application.repositories.database.commiter import Commiter


class ChatServiceProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_send_message_uc(
        self, chat_messages_repo: ChatMessagesRepo, commiter: Commiter
    ) -> SendMessageUseCase:
        return SendMessageUseCase(
            chat_messages_repo=chat_messages_repo, commiter=commiter
        )
