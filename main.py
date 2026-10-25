from caixa_eletronico.interface.menu import main


if __name__ == "__main__":
    try:
        main()

    # Ctrl+C ou fim da entrada (Ctrl+Z / Ctrl+D): encerra sem mostrar o traceback
    except (KeyboardInterrupt, EOFError):
        print("\nOperação cancelada. Saindo do caixa eletrônico...")
