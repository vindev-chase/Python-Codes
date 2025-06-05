#coding=utf-8
#Import the numpy maths library to facilitate matrix operations 
from numpy import *
from numpy import linalg as la

data_1= matrix([[0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 5],
           [0, 0, 0, 3, 0, 4, 0, 0, 0, 0, 3],
           [0, 0, 0, 0, 4, 0, 0, 1, 0, 4, 0],
           [3, 3, 4, 0, 0, 0, 0, 2, 2, 0, 0],
           [5, 4, 5, 0, 0, 0, 0, 5, 5, 0, 0],
           [0, 0, 0, 0, 5, 0, 1, 0, 0, 5, 0],
           [4, 3, 4, 0, 0, 0, 0, 5, 5, 0, 1],
           [0, 0, 0, 4, 0, 4, 0, 0, 0, 0, 4],
           [0, 0, 0, 2, 0, 2, 5, 0, 0, 1, 2],
           [0, 0, 0, 0, 5, 0, 0, 0, 0, 4, 0],
           [1, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0]])


def cosSim(inA,inB):
    num=float(inA.T*inB)
    denom=la.norm(inA)*la.norm(inB)
    return 0.5+0.5*(num/denom) #Normalise the similarity to between 0 and 1


'''Determine the value of k according to the percentage of the sum of squares of the first k singular values to the sum ofsquares of the total singular values. For subsequent SVD computation, the original matrix needs to be transformed into k-dimensional space'''
def sigmaPct(sigma,percentage):
    sigma2=sigma**2 #Square sigma 
    sumsgm2=sum(sigma2) #Calculate the sum of squares of sigma of all singular values 
    sumsgm3=0 #sumsgm3 is the sum of squares of the first k singular values 
    k=0
    for i in sigma:
        sumsgm3+=i**2
        k+=1
        if sumsgm3>=sumsgm2*percentage:
            return k

'''Parameters of the function svdEst() include: Data matrix, user number, item number, and threshold for the percentage of singular values. The rows of the data matrix correspond to the users and the columns correspond to the items, and the function is used to predict the rating of the items that have not been rated by users based on the similarity of the items'''
def svdEst(dataMat,user,simMeas,item,percentage):
    n=shape(dataMat)[1]
    simTotal=0.0;ratSimTotal=0.0
    u,sigma,vt=la.svd(dataMat)
    # The value of k is determined 
    k=sigmaPct(sigma,percentage)
    # Construct the diagonal matrix 
    sigmaK=matrix(eye(k)*sigma[:k])
    # Convert the original data to k-dimensional space (low-dimensional) according to the value of k. xformedItems represents the transformed values of items in k-dimensional space 
    xformedItems=dataMat.T*u[:,:k]*sigmaK.I
    for j in range(n):
        userRating=dataMat[user,j]
        if userRating==0 or j==item:continue
        similarity=simMeas(xformedItems[item,:].T,xformedItems[j,:].T) #Calculate the similarity between the item and the item j 
        simTotal+=similarity #Sum all similarities 
        ratSimTotal+=similarity*userRating #Multiply the 'Similarity between the item and item j' by the 'User rating of item j' and sum them 
    if simTotal==0:return 0
    else:return ratSimTotal/simTotal #Get the predicted rating for the item


'''The function recommend() produces the N recommended results with the highest predicted ratings and returns five results by default; parameters include: Data matrix, user number, similarity measurement method, predictive rating method, and the threshold for the percentage of singular values. The rows of the data matrix correspond to the users and the columns correspond to the items, and the function is used to predict the rating of the items that have not been rated by users based on the similarity of the items; the similarity measurement method uses the cosine similarity by default'''
def recommend(dataMat,user,N=5,simMeas=cosSim,estMethod=svdEst,percentage=0.9):
    unratedItems=nonzero(dataMat[user,:].A==0)[1]  #Create a list of items that have not been rated by users 
    if len(unratedItems)==0:return 'you rated everything' #Exit if all items have been rated  
    itemScores=[]
    for item in unratedItems:  #Calculate the predicted rating for each unrated item 
        estimatedScore=estMethod(dataMat,user,simMeas,item,percentage)
        itemScores.append((item,estimatedScore))
    itemScores=sorted(itemScores,key=lambda x:x[1],reverse=True)#Sort items by their rating in descending order 
    return itemScores[:N]  #Return the names of items with the top N rating values and their predicted rating values


print(recommend(data_1,5,N=3,percentage=0.8)) #Recommend the items with the top 3 ratings for users numbered 1