from chat_with_cadcoder import chat_cadcoder
from chat_with_designer_expert import designers_chat
from chat_with_designers_no_rag import norag_chat
from chat_with_designer_expert_with_rag import designers_rag_chat
from chat_with_designers_autogen_rag import rag_chat

def display_chat_options():
    print("Welcome to the CAD Design AI Chatbot!")
    print("Please select one of the agentic chats to create CAD models:")

    print("1. Single agent chat with CAD coder")
    print("2. Chat with multi agent team without RAG")
    print("3. Chat with multi agent team with RAG")
    print("4. Chat with multi agent team with autogen RAG")
    print("5. Chat with CAD coder and reviewer agents without RAG")

    while True:
        try:
            user_choice = input("Enter the number of your choice: ")
            if 1 <= int(user_choice) <= 5:
                return user_choice
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_user_choice():
    while True:
        user_input = input("Do you want to use the default llm configuration? (Y/Yes/N/No): ").strip().lower()
        if user_input in ["y", "yes"]:
            return "default"
        elif user_input in ["n", "no"]:
            return "custom"
        else:
            print("Invalid input. Please enter 'Y/Yes' for default or 'N/No' for custom configuration.")



# Call the main function to start the application

def main():
    print("\nLet's create CAD models!")
    print("-------------------")
    print("Enter 'exit' to exit the program")
    choice= display_chat_options()
    while True:
        try:
            prompt = input("\nEnter your design problem (or 'exit'if you want to exit): ")
            if prompt.lower() == 'exit':
                print("\nExiting CAD Design Assistant")
                break
            try:
                if choice == "1":
                    chat_cadcoder(prompt)
                elif choice == "2":
                    designers_chat(prompt)
                elif choice == "3":
                    designers_rag_chat(prompt)
                elif choice == "4":
                    rag_chat(prompt)
                elif choice == "5":
                    norag_chat(prompt)
                else:
                    print("Invalid choice. Please select a valid option.")
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Please try again.")
            
        except KeyboardInterrupt:
            print("\nSession interrupted by user")
            break
        except ValueError as ve:
            print(f"\nError: {str(ve)}")
            print("Please try again with a more detailed prompt")
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try again or create github issues if the problem persists")

if __name__ == "__main__":
    main()
