from plaguefire.core.GameSession import GameSession


def main() -> None:
    session = GameSession()

    print("PLAGUEFIRE")
    print("Type help for commands.")

    while True:
        command = input("\nplaguefire> ")
        result = session.handle_command(command)

        if result.text:
            print(result.text)

        if result.should_quit:
            break


if __name__ == "__main__":
    main()
