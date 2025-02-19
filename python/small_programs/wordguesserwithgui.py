from tkinter import *

app=Tk()
Label(app,text="hello world").grid(row=0)
Label(app,text="name").grid(row=1)
name=Entry(app).grid(row=1,column=1)
Button(app,text="press me ",command=name).grid(row=2,column=1)
app.mainloop()