# Library management system

#---------------------------menu----------------------
def menu():
    print("please enter any of these commands:")
    print("menu : to access menu")
    print("help : to access help or support")
    print("quit : to exit the program")
    print("allbooks : to access list of all books")
#---------------------------help----------------------
def help():
    pass
#--------------------allbooks------------------
def allbooks():
    pass
# ---------------------------------------------------------------list of books---------------------------------------
books = {
    1: {"title": "The Very Hungry Caterpillar", "author": "Eric Carle", "genre": "Picture Book, Fiction"},
    2: {"title": "Where the Wild Things Are", "author": "Maurice Sendak", "genre": "Picture Book, Fantasy"},
    3: {"title": "Corduroy", "author": "Don Freeman", "genre": "Picture Book, Fiction"},
    4: {"title": "Click, Clack, Moo: Cows That Type", "author": "Doreen Cronin", "genre": "Picture Book, Humor"},
    5: {"title": "The Giving Tree", "author": "Shel Silverstein", "genre": "Picture Book, Fiction"},
    6: {"title": "Goodnight Moon", "author": "Margaret Wise Brown", "genre": "Picture Book, Bedtime Story"},
    7: {"title": "The Cat in the Hat", "author": "Dr. Seuss", "genre": "Picture Book, Humor"},
    8: {"title": "Brown Bear, Brown Bear, What Do You See?", "author": "Bill Martin Jr.", "genre": "Picture Book, Animals"},
    9: {"title": "Chicka Chicka Boom Boom", "author": "Bill Martin Jr.", "genre": "Picture Book, Alphabet"},
    10: {"title": "Curious George", "author": "Margret & H.A. Rey", "genre": "Picture Book, Animals"}
}

#user interaction-----------------

user=input("please enter your name to continue => ")

print("hello ",user," welcome to our library ")
print("type menu command to access the menu")
choice=""
run=True
while run:
    choice=input("(type quit to exit )command => ")

    if choice=="menu":
        menu()
    elif choice=="help":
        help()
    elif choice=="list":
        allbooks()
    elif choice=="quit":
        run=False
print("thank you for visiting , take care ",user)