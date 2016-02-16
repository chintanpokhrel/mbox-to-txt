import mailbox
import re


def munge_message(text):
    """
    Munge an e-mail message (in text form).

    :param text: The e-mail message.
    :return: The munged e-mail message.
    """
    text = re.sub(r'(\n|^)On.*\n?.*wrote:\n+(.|\n)*$', '', text)
    text = re.sub(r'(\n|^)From:(.|\n)*$', '', text)
    text = re.sub(r'(\n|^)---------- Forwarded message ----------(.|\n)*$', '', text)
    text = re.sub(r'(\n|^)-----BEGIN PGP MESSAGE-----\n(.|\n)*-----END PGP MESSAGE-----\n', '', text)
    text = re.sub(r'<[^ ]+>', '', text)
    return text


def unquoted_line(line):
    """
    Unquote an e-mail message line according to RFC 3676.

    :param line: The (possibly quoted) message line.
    :return: (unquoted line, quote depth).
    """
    quote_depth = 0
    while line.startswith('>'):
        line = line[1:]
        quote_depth += 1
    return (line, quote_depth)


def unstuff_line(line):
    """
    Unstuff an e-mail message line according to RFC 3637.

    :param line: The (possibly stuffed) message line.
    :return: The unstuffed message line.
    """
    if line.startswith(' '):
        return line[1:]
    return line


def unflow_line(line, delsp):
    """
    Unflow an e-mail message line according to RFC 3637.

    :param line: The (possibly soft-broken) message line.
    :param delsp: Whether or not soft-break spaces should be deleted.
    :return: (processed line, soft-broken)
    """
    if len(line) < 1:
        return (line, False)
    if line.endswith(' '):
        if delsp:
            line = line[:-1]
        return (line, True)
    return (line, False)


def unflow_text(text, delsp):
    """
    Unflow an e-mail message according to RFC 3637.

    :param text: The flowed message.
    :param delsp: Whether or not soft-break spaces should be deleted.
    :return: The processed message.
    """
    full_line = ''
    full_text = ''
    lines = text.splitlines()
    for line in lines:
        (line, quote_depth) = unquoted_line(line)
        line = unstuff_line(line)
        (line, soft_break) = unflow_line(line, delsp)
        full_line += line
        if not soft_break:
            full_text += '>' * quote_depth + full_line + '\n'
            full_line = ''
    return full_text


def part_to_text(part):
    """
    Converts an e-mail message part into text.

    Returns None if the message could not be decoded as ASCII.

    :param part: E-mail message part.
    :return: Message text.
    """
    if part.get_content_type() != 'text/plain':
        return None
    charset = part.get_content_charset()
    if not charset:
        return None
    text = str(part.get_payload(decode=True), encoding=charset, errors='ignore')
    try:
        text = str(text.encode('ascii'), 'ascii')
    except UnicodeEncodeError:
        return None
    except UnicodeDecodeError:
        return None
    if part.get_param('format') == 'flowed':
        text = unflow_text(text, part.get_param('delsp', False))
    return text


def message_to_text(message):
    """
    Converts an e-mail message into text.

    Returns an empty string if the e-mail message could not be decoded as ASCII.

    :param message: E-mail message.
    :return: Message text.
    """
    text = ''
    for part in message.walk():
        part = part_to_text(part)
        if part:
            text += part
    return text


def print_mailbox(mailbox, author):
    """
    Print the contents of a mailbox to standard-out, excluding messages to 'author' and not from 'author'.

    :param mailbox: Mailbox to print.
    :param author: Excludes messages to and not from this author.
    :return: Nothing.
    """
    for message in mailbox:
        if not message['From']:
            continue
        if author not in message['From']:
            continue
        if not message['To']:
            continue
        if author in message['To']:
            continue
        text = message_to_text(message)
        text = munge_message(text)
        if text and len(text) > 0:
            print(text)


def main():
    mb = mailbox.mbox('Sent.mbox', create=False)
    print_mailbox(mb, '<sydius@gmail.com>')


if __name__ == '__main__':
    main()