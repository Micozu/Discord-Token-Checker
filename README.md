# Discord Token Checker

A multi-threaded Discord token checker script that verifies the validity of tokens, retrieves Nitro status, checks for payment methods, and determines server ownership. 

## Features

- **Token Validation**: Check the validity of Discord tokens.
- **Nitro Status**: Display the Nitro subscription level.
- **Payment Method Check**: Identify if payment methods are linked to the account.
- **Server Ownership**: Highlight if the user owns any Discord servers.
- **Threaded Execution**: Process tokens concurrently for faster execution.
- **Output Logs**:
  - Valid tokens with detailed information are saved to `valid_tokens.txt`.
  - Invalid tokens are saved to `invalid_tokens.txt`.

## Requirements

- Python 3.7 or newer
- The following Python libraries:
  - `requests`
  - `colorama`
  - `itertools`

## Paste your discord tokens to: tokens.txt
