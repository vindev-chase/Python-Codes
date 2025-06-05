def init():
  global graph
  graph.append([-1,  -1, -1, -1, -1, -1,  -1])
  graph.append([-1,  0, 0, -1, 0, 0,  -1])
  graph.append([-1,  0, -1, 0, 0, 0,  -1])
  graph.append([-1,  0, -1, 0, -1, -1,  -1])
  graph.append([-1,  0, -1, 0, 0, 0,  -1])
  graph.append([-1,  0, 0, 0, -1, 0,  -1])
  graph.append([-1,  0, 0, 0, 0, 0,  -1])
  graph.append([-1,  -1, -1, -1, -1, -1,  -1])
#Depth-first traversal 
def deepFirstSearch( steps , x, y ):
  global graph
  current_step = steps + 1
  print(x, y, current_step )
  graph[x][y] = current_step
  next_step = current_step + 1

  if not(x-1== 1 and y==1) and graph[x-1][y] != -1 and ( graph[x-1][y]>next_step or graph[x-1][y] ==0 ) : #Left 
    deepFirstSearch(current_step, x-1 , y )
  if not(x == 1 and y-1==1) and graph[x][y-1] != -1 and ( graph[x][y-1]>next_step or graph[x][y-1] ==0 ) : #Top 
    deepFirstSearch(current_step, x , y-1 )
  if not(x == 1 and y+1==1) and graph[x][y+1] != -1 and ( graph[x][y+1]>next_step or graph[x][y+1]==0 ) : #Bottom 
    deepFirstSearch(current_step, x , y+1 )
  if not(x+1== 1 and y==1) and graph[x+1][y] != -1 and ( graph[x+1][y]>next_step or graph[x+1][y]==0 ) : #Right 
    deepFirstSearch(current_step, x+1 , y )
if __name__ == "__main__":
  graph = []
  init()
  deepFirstSearch(-1,1,1)
  print(graph[1][5])