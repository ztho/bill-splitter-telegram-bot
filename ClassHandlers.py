class Person:
    def __init__(self, name, index = 0):
        self.name = name
        self.orders = []
        self.index = index

    def getName(self):
        return self.name

    def getOrders(self):
        return self.orders

    def getOrdersAsString(self):
        sb = ""
        for order in self.orders:
            sb += order.orderName + "\n"
        return sb

    def addOrder(self, newOrder):
        self.orders.append(newOrder)

    def getTotalPrice(self):
        totalPrice = 0.0
        for order in self.orders:
            totalPrice += order.price
        return totalPrice

class Order:
    def __init__(self, orderName, price = 0):
        self.orderName = orderName
        self.price = price

    def setPrice(self, price):
        self.price = price

class Bill:
    def __init__(self):
        self.nameList = []
        self.splitWithIndexes = []
        self.hasStart = False
   
    # Assigns index to each person in name list
    def assignIndex(self):
        i = 0
        for person in self.nameList:
            person.index = i 
            i += 1
    
    # Find index of person based on name, return -1 if not found
    def findIndex(self, targetName):
        for person in self.nameList:
            if(targetName == person.getName()):
                return person.index
        return -1 

    def add_name_to_nameList(self, name):
        self.nameList.append(Person(name))
    
    def assign_order_to_person(self, index, order):
        person = self.nameList[index]
        person.addOrder(order)
    
    # Assigns the split order to indexes selected
    def add_to_splitWithIndexes(self, name):
        index = self.findIndex(name)
        self.splitWithIndexes.append(index)
    
    # Assigns everyone the split order
    def add_all_to_splitWithIndexes(self):
        i = 0 
        while i < len(self.nameList):
            self.splitWithIndexes.append(i)
            i += 1

    # Computes the price based on the number of people to split with
    def split_price_computation(self, order):
        perPersonPrice = order.price/len(self.splitWithIndexes)
        nameOfOrder = order.orderName + " (Split Among "
        for index in self.splitWithIndexes:
            nameOfOrder += self.nameList[index].getName() + ", "
        nameOfOrder = nameOfOrder[:-2]
        nameOfOrder += ")"
        splitOrder = Order(nameOfOrder, perPersonPrice)
        for index in self.splitWithIndexes:
            self.assign_order_to_person(index, splitOrder)
        
        del self.splitWithIndexes[:]

    def add_GST(self, gst_amount):
        gst_amount_decimal = float(gst_amount)/100
        for person in self.nameList:
            gstPrice = person.getTotalPrice() * gst_amount_decimal 
            person.addOrder(Order("GST (" + gst_amount + "%) ", gstPrice))
    
    def add_service_charge(self, svc_amount):
        svc_decimal = float(svc_amount)/100
        for person in self.nameList:
            svcPrice = person.getTotalPrice() * svc_decimal
            person.addOrder(Order("Service Charge (" + svc_amount + "%) ", svcPrice))
    
    def viewNameList(self):
        sb = "<b>Namelist</b>\n"
        i = 1
        for name in self.nameList:
            sb += str(i) + ". " + name.getName() + "\n"
            i += 1
        return sb
    
    # Removes people from name list. Return True if executed, or False if name not found
    def delete_name_from_list(self, name):
        index = self.findIndex(name)
        if(index != -1):
            del self.nameList[index]
            self.assignIndex()
            return True
        else:
            return False

    def generate_receipt(self): 
        output = "<b>Receipt\n\n</b>"
        totalPrice = 0
        for person in self.nameList:
            output += "<b>" + person.getName() + "'s orders:</b>\n"
            i = 1
            for order in person.orders:
                output += str(i) +  ". " + order.orderName + ": " + str("%0.2f" % order.price) + "\n"
                i += 1
            output += ("---<i>Total Payable: $" + str("%0.2f" % person.getTotalPrice())
                        + "</i>\n\n")
            totalPrice += person.getTotalPrice()
        output += "-----------------------------------------------------\n"
        output += "<i>Bill Total: $" + str("%0.2f " % totalPrice) +"</i>\n"
        
        return output
    
    def clear_bill(self):
        del self.nameList[:]
        del self.splitWithIndexes[:]
