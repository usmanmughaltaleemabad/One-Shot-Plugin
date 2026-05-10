"""
Notification Handler - Job event notifications

Generates:
- Email notifications
- Slack notifications
- SMS notifications (future)
- Push notifications (future)
- Notification templates
"""

from typing import Dict, Any


class NotificationHandler:
    """Generate notification code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_python_notifications(self) -> str:
        """Generate Python notification handlers"""
        return """
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)

class EmailNotifier:
    '''Send email notifications'''

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send(self, to_email: str, subject: str, body: str, html: bool = False):
        '''Send email notification'''
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = to_email

            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f'Email sent to {to_email}')
        except Exception as e:
            logger.error(f'Email send failed: {e}')

class SlackNotifier:
    '''Send Slack notifications'''

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, message: str, channel: Optional[str] = None, username: str = 'JobBot'):
        '''Send Slack notification'''
        import requests

        payload = {
            'text': message,
            'username': username
        }

        if channel:
            payload['channel'] = channel

        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 200:
                logger.info('Slack notification sent')
            else:
                logger.error(f'Slack notification failed: {response.status_code}')
        except Exception as e:
            logger.error(f'Slack notification error: {e}')

    def send_rich(self, title: str, text: str, color: str = '#36a64f',
                  fields: dict = None):
        '''Send rich Slack notification with blocks'''
        import requests

        blocks = [
            {
                'type': 'header',
                'text': {'type': 'plain_text', 'text': title}
            },
            {
                'type': 'section',
                'text': {'type': 'mrkdwn', 'text': text}
            }
        ]

        if fields:
            for label, value in fields.items():
                blocks.append({
                    'type': 'section',
                    'fields': [
                        {'type': 'mrkdwn', 'text': f'*{label}*'},
                        {'type': 'mrkdwn', 'text': str(value)}
                    ]
                })

        payload = {'blocks': blocks}

        try:
            requests.post(self.webhook_url, json=payload)
            logger.info('Rich Slack notification sent')
        except Exception as e:
            logger.error(f'Rich notification error: {e}')

class NotificationManager:
    '''Manage notifications for job events'''

    def __init__(self):
        self.email_notifier: Optional[EmailNotifier] = None
        self.slack_notifier: Optional[SlackNotifier] = None
        self.subscribers = {}  # event -> list of (notifier_type, config)

    def configure_email(self, smtp_host: str, smtp_port: int, username: str, password: str):
        '''Configure email notifications'''
        self.email_notifier = EmailNotifier(smtp_host, smtp_port, username, password)

    def configure_slack(self, webhook_url: str):
        '''Configure Slack notifications'''
        self.slack_notifier = SlackNotifier(webhook_url)

    def subscribe(self, event: str, notifier_type: str, config: dict):
        '''Subscribe to job event notifications'''
        if event not in self.subscribers:
            self.subscribers[event] = []

        self.subscribers[event].append({
            'type': notifier_type,
            'config': config
        })

        logger.info(f'Subscribed to {event} with {notifier_type}')

    def notify(self, event: str, job_id: str, data: dict):
        '''Send notifications for event'''
        if event not in self.subscribers:
            return

        for subscriber in self.subscribers[event]:
            self._send_notification(subscriber, event, job_id, data)

    def _send_notification(self, subscriber: dict, event: str, job_id: str, data: dict):
        '''Send individual notification'''
        notifier_type = subscriber['type']
        config = subscriber['config']

        if notifier_type == 'email' and self.email_notifier:
            subject = f'Job {job_id} - {event}'
            body = self._format_email(event, job_id, data)
            self.email_notifier.send(config['email'], subject, body)

        elif notifier_type == 'slack' and self.slack_notifier:
            message = self._format_slack(event, job_id, data)
            self.slack_notifier.send(message, config.get('channel'))

    def _format_email(self, event: str, job_id: str, data: dict) -> str:
        '''Format email message'''
        return f'''
Job Event: {event}
Job ID: {job_id}
Timestamp: {data.get('timestamp', 'N/A')}

Details:
{json.dumps(data, indent=2)}
'''

    def _format_slack(self, event: str, job_id: str, data: dict) -> str:
        '''Format Slack message'''
        return f'*Job {event}*: {job_id}'

# Global notification manager
notification_manager = NotificationManager()

def notify_job_event(event: str, job_id: str, **kwargs):
    '''Notify subscribers of job event'''
    notification_manager.notify(event, job_id, kwargs)

# Example usage:
# notification_manager.configure_email('smtp.gmail.com', 587, 'user@gmail.com', 'password')
# notification_manager.configure_slack('https://hooks.slack.com/services/...')
# notification_manager.subscribe('job.completed', 'email', {'email': 'admin@example.com'})
# notification_manager.subscribe('job.failed', 'slack', {'channel': '#alerts'})
"""

    def generate_nestjs_notifications(self) -> str:
        """Generate NestJS notification handlers"""
        return """
import { Injectable } from '@nestjs/common';
import axios from 'axios';
import * as nodemailer from 'nodemailer';

@Injectable()
export class EmailService {
    private transporter: any;

    constructor(
        private host: string,
        private port: number,
        private user: string,
        private pass: string
    ) {
        this.transporter = nodemailer.createTransport({
            host: this.host,
            port: this.port,
            secure: true,
            auth: { user: this.user, pass: this.pass },
        });
    }

    async send(to: string, subject: string, html: string): Promise<void> {
        try {
            await this.transporter.sendMail({
                from: this.user,
                to,
                subject,
                html,
            });
            console.log(`Email sent to ${to}`);
        } catch (error) {
            console.error('Email send failed:', error);
        }
    }
}

@Injectable()
export class SlackService {
    constructor(private webhookUrl: string) {}

    async send(message: string, channel?: string): Promise<void> {
        const payload: any = { text: message };
        if (channel) payload.channel = channel;

        try {
            await axios.post(this.webhookUrl, payload);
            console.log('Slack notification sent');
        } catch (error) {
            console.error('Slack notification failed:', error);
        }
    }

    async sendRich(
        title: string,
        text: string,
        fields?: Record<string, string>
    ): Promise<void> {
        const blocks: any[] = [
            { type: 'header', text: { type: 'plain_text', text: title } },
            { type: 'section', text: { type: 'mrkdwn', text } },
        ];

        if (fields) {
            const fieldBlocks = Object.entries(fields).map(([label, value]) => ({
                type: 'section',
                fields: [
                    { type: 'mrkdwn', text: `*${label}*` },
                    { type: 'mrkdwn', text: value },
                ],
            }));
            blocks.push(...fieldBlocks);
        }

        try {
            await axios.post(this.webhookUrl, { blocks });
            console.log('Rich Slack notification sent');
        } catch (error) {
            console.error('Rich notification failed:', error);
        }
    }
}

@Injectable()
export class NotificationManager {
    private subscribers: Map<string, any[]> = new Map();

    constructor(
        private emailService?: EmailService,
        private slackService?: SlackService
    ) {}

    subscribe(
        event: string,
        notifierType: 'email' | 'slack',
        config: Record<string, any>
    ): void {
        if (!this.subscribers.has(event)) {
            this.subscribers.set(event, []);
        }

        this.subscribers.get(event).push({
            type: notifierType,
            config,
        });

        console.log(`Subscribed to ${event} with ${notifierType}`);
    }

    async notify(
        event: string,
        jobId: string,
        data: Record<string, any>
    ): Promise<void> {
        if (!this.subscribers.has(event)) return;

        for (const subscriber of this.subscribers.get(event)) {
            await this.sendNotification(subscriber, event, jobId, data);
        }
    }

    private async sendNotification(
        subscriber: any,
        event: string,
        jobId: string,
        data: Record<string, any>
    ): Promise<void> {
        const { type, config } = subscriber;

        if (type === 'email' && this.emailService) {
            const subject = `Job ${jobId} - ${event}`;
            const html = `<p>Job: ${jobId}</p><p>Event: ${event}</p><pre>${JSON.stringify(data, null, 2)}</pre>`;
            await this.emailService.send(config.email, subject, html);
        } else if (type === 'slack' && this.slackService) {
            const message = `*Job ${event}*: ${jobId}`;
            await this.slackService.send(message, config.channel);
        }
    }
}

export async function notifyJobEvent(
    event: string,
    jobId: string,
    notificationManager: NotificationManager,
    data?: Record<string, any>
): Promise<void> {
    await notificationManager.notify(event, jobId, data || {});
}
"""


def generate_notification_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate notification handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = NotificationHandler(framework, language)
    output = {}

    if language == "python":
        output["notifications.py"] = generator.generate_python_notifications()
    elif language == "javascript":
        output["notifications.service.ts"] = generator.generate_nestjs_notifications()

    return output
