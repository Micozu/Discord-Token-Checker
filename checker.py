import requests
import threading
import queue
import os
from colorama import init, Fore, Style
import itertools

# Initialize colorama
init(autoreset=True)

# Number of threads to use for checking tokens
NUM_THREADS = 10

# API endpoints
DISCORD_API_URL = "https://discord.com/api/v10/users/@me"
DISCORD_BILLING_PAYMENT_SOURCES_URL = "https://discord.com/api/v10/billing/payment-sources"
DISCORD_GUILDS_URL = "https://discord.com/api/v10/users/@me/guilds"

# Create a global print lock
print_lock = threading.Lock()

def load_tokens(file_path):
    """
    Load tokens from a text file, one per line.
    """
    if not os.path.exists(file_path):
        with print_lock:
            print(f"{Fore.YELLOW}Warning: File {file_path} does not exist.{Style.RESET_ALL}")
        return []
    with open(file_path, 'r') as file:
        tokens = [line.strip() for line in file if line.strip()]
    return tokens

def get_nitro_status(premium_type):
    """
    Convert premium_type integer to a human-readable Nitro status.
    """
    nitro_status = {
        0: f"{Fore.RED}No Nitro{Style.RESET_ALL}",
        1: f"{Fore.GREEN}Nitro Classic{Style.RESET_ALL}",
        2: f"{Fore.GREEN}Nitro{Style.RESET_ALL}"
    }
    return nitro_status.get(premium_type, f"{Fore.YELLOW}Unknown{Style.RESET_ALL}")

def has_payment_method(token):
    """
    Check if the account has any payment methods linked.
    Returns True if at least one payment method exists, else False.
    """
    headers = {
        "Authorization": token
    }
    try:
        response = requests.get(DISCORD_BILLING_PAYMENT_SOURCES_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            payment_sources = response.json()
            # Assuming payment_sources is a list of payment methods
            return len(payment_sources) > 0
        else:
            # If the endpoint is unauthorized or not found, assume no payment methods
            return False
    except requests.exceptions.RequestException:
        # In case of any request exceptions, assume no payment methods
        return False

def check_server_ownership(token):
    """
    Check if the user owns any server (guild).
    If yes, display "[SERVER OWNED]" in rainbow colors.
    """
    headers = {
        "Authorization": token
    }
    try:
        response = requests.get(DISCORD_GUILDS_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            guilds = response.json()
            for guild in guilds:
                if guild.get('owner', False):
                    return True  # User owns at least one server
        return False
    except requests.exceptions.RequestException:
        return False

def rainbow_text(text):
    """
    Rainbowify text by cycling through colors.
    """
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    return ''.join(f"{color}{char}" for char, color in zip(text, itertools.cycle(colors)))

def check_token(token, valid_tokens, invalid_tokens):
    """
    Check if a Discord token is valid by making a request to the Discord API.
    Additionally, check if the user has Nitro and any payment methods linked.
    """
    headers = {
        "Authorization": token
    }
    try:
        response = requests.get(DISCORD_API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            user = response.json()
            username = user.get('username', 'Unknown')
            discriminator = user.get('discriminator', '0000')
            premium_type = user.get('premium_type', 0)
            nitro_status = get_nitro_status(premium_type)
            
            # Check for payment methods
            payment_method_exists = has_payment_method(token)
            card_indicator = f" {Fore.CYAN}[CARD!]{Style.RESET_ALL}" if payment_method_exists else ""

            # Check if the user owns any servers
            server_owned = check_server_ownership(token)
            server_owned_indicator = f" {rainbow_text('[SERVER OWNED]')}" if server_owned else ""

            with print_lock:
                print(f"{Fore.GREEN}[VALID]{Style.RESET_ALL} {token} - User: {username}#{discriminator} - Nitro: {nitro_status}{card_indicator}{server_owned_indicator}")
            
            # Store token along with Nitro status and payment method indicator
            valid_tokens.append((token, nitro_status, payment_method_exists, server_owned))
        else:
            # Append to invalid_tokens without printing
            invalid_tokens.append(token)
    except requests.exceptions.RequestException:
        # Append to invalid_tokens without printing
        invalid_tokens.append(token)

def worker(token_queue, valid_tokens, invalid_tokens):
    """
    Worker thread to process tokens from the queue.
    """
    while True:
        try:
            token = token_queue.get_nowait()
        except queue.Empty:
            return
        check_token(token, valid_tokens, invalid_tokens)
        token_queue.task_done()

def main():
    tokens_file = "tokens.txt"
    tokens = load_tokens(tokens_file)
    if not tokens:
        with print_lock:
            print(f"{Fore.YELLOW}No tokens to check.{Style.RESET_ALL}")
        return

    token_queue = queue.Queue()
    for token in tokens:
        token_queue.put(token)

    valid_tokens = []
    invalid_tokens = []
    threads = []

    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=worker, args=(token_queue, valid_tokens, invalid_tokens))
        thread.start()
        threads.append(thread)

    # Wait for all tasks to be completed
    token_queue.join()

    # Optionally, wait for all threads to finish
    for thread in threads:
        thread.join()

    # Write valid tokens to a file with Nitro status and payment method indicator
    if valid_tokens:
        with open("valid_tokens.txt", "w") as file:
            for token, nitro, card, server_owned in valid_tokens:
                card_text = "CARD!" if card else "No Card"
                server_owned_text = "SERVER OWNED" if server_owned else "No Server"
                file.write(f"{token} - Nitro: {nitro} - Card: {card_text} - {server_owned_text}\n")
        with print_lock:
            print(f"\n{Fore.GREEN}Valid tokens have been saved to valid_tokens.txt{Style.RESET_ALL}")
    else:
        with print_lock:
            print(f"\n{Fore.RED}No valid tokens found.{Style.RESET_ALL}")

    # Write invalid tokens to a separate file without printing them
    if invalid_tokens:
        with open("invalid_tokens.txt", "w") as file:
            for token in invalid_tokens:
                file.write(f"{token}\n")
        with print_lock:
            print(f"{Fore.RED}Invalid tokens have been saved to invalid_tokens.txt{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
