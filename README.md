# 我的某一次编译原理练习项目

这个项目是我在做完上一个名为[van_shell](https://github.com/mingshuo-van/van_shell#)的练手项目后，学了一段时间编译原理后试着写的。

依旧是基于python，因为它可以让我更专注于逻辑实现。

控制流有while , break , continue , if-elif-else，且可以任意嵌套

我在这次尝试了闭包的实现，包括简单的一个逃逸分析，让闭包不会浪费太多内存。

在这里，我采用了C风格的语法。包括大括号来框定代码块，以及C的&& || 等特点

不过还有大量的python风格的体现，比如单行注释用 `#`，分浮点除法`/`和整型除法`//`

特殊地，前置`!`是逻辑非，后置`!`是阶乘，!6! 等价于 !(6!)也就是 !720 => false

尤为特殊的是，我设计了几种功能不同的赋值符号。除了普通的 = 外，它们分别是:

- `:=`:这个符号可以简单理解为python的nonlocal，左值必须是外层已经创建的变量
  - `n := n - 2`:引用外层的n并同时把n减去2
  - `arr := arr`:不修改arr，只是声明要在本层使用外层的同一个arr
    - 尤为值得说明的是，如果你直接写 `return arr` 而不先用 `arr := arr`声明使用外层或用`arr = []`定义本层，是不行的
- `=>`:这个符号可以简单理解为python的global，左值必须是在全局作用域创建的变量
- `?=`:这个符号我成为惰性单次赋值符号，放在函数里用会比较好用
  - 比如 `x ?= test()`，放在函数里执行第一遍后会真正运行test()获得一个值，此后不管运行多少遍都会是第一次的test()的结果
  - 也就是说，你可以把它和闭包放在一起做类似静态变量的用法，这一点在后文会有展示
  - 特殊说明一个特殊行为：
  ```text
    if(a){
    x ?= test()
    }else{
    x ?= test()
    }
    ```
  - 如果上面的代码在一个循环中反复执行的话，且a会在真假中改变
  - 那么 a 为 true 或者 false 时，test()的值会分别存储在各自的语句节点里
  - 在第一个执行if时，x获得了一个初始值，后面多次执行if，a都是第一次那个引用（如果是可变对象，修改是积累的）
  - 如果中间有一次执行了else，那x会获得另一个初始值，并且也是积累修改的
  - 中间如果又执行了if，那最开始的那个if获得的值也不会丢失，而是继承回来

### exe文件的使用方法：

ast address 可以在address的父目录下生成一份同名的ast文件

run address 可以执行address对应的ast文件

exit 可以退出程序，请注意和代码文件中允许的exit()的区别，后者是结束代码程序而非结束解释器程序

把程序直接拖到exe上可以直接执行，不限制ast或者其他类型

非ast会自动生成ast

支持一次运行多个文件

下面是一个展示代码，任何人都可以通过阅读或运行来理解解释器的语法规则。

`欢迎大家使用、提出建议或者和作者交流！`

```text
print('基础类型赋值与展示')
a = 10
b = 12.5
c = 1e4
d = 1/1e7
e = [1,2,3,[4,5,6],{'hello':1,'world':2}]
f = {1:'1',2:'2',3:'3','list':e}
g = 'this is a test \n and line'
print(a)
print(b)
print(c)
print(d)
print(e)
print(f)
print(g)
print('='*120)


print('函数定义、闭包与操作全局变量')

global_num = 100

fn num(){
    global_num => global_num + 10 # => 赋值符号声明操作的是全局的global_num
    return -1
}

fn outer(){
    n = 10
    fn inner(){
        n := n - 2 # := 赋值符号声明操作的是外界的n
        return n
    }
    return inner
}

inner = outer()
print(inner())
print(inner())
print(inner())
print(num())
print(num())
print(num())
print(global_num)
print(print)
print('='*120)
old_f = f
fn outer(){
    a = 1
    while (a){
        a = 0
        print(a)
        n = '十'
    }
    vars()
    print(n)
    fn inner(){
        n := n
        return n
    }
    return inner
}
f = outer()
print(f())


fn outer(){
    n = -20
    fn inner(){
        if (1){
            a = true
            while (a){
            a = false
            if(1){ n:= n}
            }
        }
        return n
    }
    return inner
}
print(outer()())

fn outer(){
    n = -8
    fn inner(){
        fn inner_inner(){
            n := n
            x = n
            return x
        }
        return inner_inner
    }
    return inner
}
f = outer()
print(f()())
f = old_f
print('='*120)

print('list 和 dict 的左值和右值使用，切片')
a = e[0]
b = e[-1]['hello']
c = f['list'][3][2]
d = f
d['list'] = 0
e[0] = 100
e[1] = ['this','is','van']
print(a)
print(b)
print(c)
print(d)
print(e)
print(f)
print(e[:])
a = 1
b = 23
x = {a+b:1}
print(x)
a = 5
print(x)
print('='*120)

print('特殊!的声明，前置为逻辑非，后置为阶乘 同时出现时阶乘优先计算')
x = 6
print(!true)
print(!false)
print(!x)
print(x!)
print(!x!)
print('='*120)

print('list 和 dict 与闭包的结合，惰性单次符号 ?=')
fn outer0(n){
    fn inner0(m){
        n := n + m
        return n
    }
    return inner0
}
fn outer1(n){
    temp = outer0(n)
    fn inner1(m){
        x = temp(m)
        return x
    }
    return inner1
}
print(outer0(100)(-10))
print(outer1(110)(-10))
print(outer1(100)(50))
t = outer1(100)
print(t(30))
print(t(20))
fn outer(){
    n = 6
    fn inner(){
        n := n - 4
        return n
    }
    return inner
}
arr = [outer()]
print(arr[0]())
fn out(){
    arr = [[1,2,3,4,5,outer()],1,2,3,4,5]
    fn inner(){
        arr := arr
        return arr
    }
    return inner
}
fn num(){
    return -1
}
print(out()()[0][num()]())
print('out()()[0][num()]() == '+out()()[0][num()]())
x = out()()[0][num()]()
print('x is '+x)
print('x! is ' + x!)
print(out()()[0][num()]()!)
print(out()()[0])
print(out()()[0][out()()[0][num()]()])
arr = out()()
print(arr)
print(arr[0])
print(arr[out()()[0][num()]()!])
print(out()()[out()()[0][num()]()!])
fn base(){
    n = 10
    fn i(){
        n := n - 2
        return n
    }
    return i
}

fn test(){
    m ?= base() # 第一次执行时赋值，只计算一次
    fn inner(){
        m := m
        return m
    }
    return inner
}
print('第一种，会共享')
print(test()()())
print(test()()())
print(test()()())
print(test()()())
fn test(){
    m = base()
    fn inner(){
        m := m
        return m
    }
    return inner
}
print('第二种，不会共享')
print(test()()())
print(test()()())
print(test()()())
print(test()()())
print('='*120)


print('while for if 流程控制')

i = 0
limit = 30

while(true){
    i = i + 1
    if (i>= limit){
        t = 10
        x = 8
        while(t){
            t = t - 1
            if (t < x){
                break
            }
            print('inner!')
        }
        break
    }
    if (i%10 == 0){
        print('i % 10 == 0')
    }
    if(i&7){
        print('i&7 != 0')
        continue
    }
    print('get here')
}
print('i is ' + i)
if(0 || 1){
    print('or')
}
if(1 && 2){
    print('and')
}
flag = 2
if(0){
    print(0)
}elif(flag == 1){
    print(1)
}elif(flag == 2){
    print(2)
}else{
    print(3)
}

i = 'num'
for i in (3){
    print(i)
}
for i in (-1,4){
    print(i)
}
e = 3
fn num(){
    return 0
}
for i in (e,num(),-1){
    print(i)
}
print(i)
print('='*120)

print('函数的递归')

fn ack(m,n){
    if(m == 0){
        return n + 1
    }
    if(n == 0){
        return ack(m-1,1)
    }
    return ack(m-1,ack(m,n-1))
}
print('ack(0,3) is ' + ack(0,3))
print('ack(3,2) is ' + ack(3,2))
print('ack(3,3) is ' + ack(3,3))
print('ack(3,4) is ' + ack(3,4))

fn move(a,b){
    print('move from ' + a + ' to ' + b)
}

fn hanoi(a,b,c,n){
    if (n==1){
        move(a,c)
        return null
    }
    hanoi(a,c,b,n-1)
    move(a,c)
    hanoi(b,a,c,n-1)
}
print('hanoi when n is ' + 3)
hanoi('left','mid','right',3)
print('hanoi when n is ' + 4)
hanoi('left','mid','right',4)
print('='*120)


print('其他运算符')

a = 35
b = 20
print(a+b)
print(a-b)
print(a*b)
print(a/b)
print(a//b)
print(a%b)
print(a**b)
print(a&b)
print(a|b)
print(a^b)
print(~b)
print(a>b)
print(a>=b)
print(a<b)
print(a<=b)
print(a==b)
print(a!=b)

print('='*120)

print('其他部分内置函数')
print(list())
print(dict())
print(str(12345))
print(bool(23))
print('world')
print(list('world'))
t = list('world')
print(t)
res = pop(t,-1)
print('res is '+res)
print(t)
push(t,'d')
print(t)
d = {'1':1,'2':2}
print(d)
pop(d,'1')
print(d)
print(has(d,'1'))
print(has(d,'2'))
print(has(t,'w'))
d['test'] = 1
d['apple'] = 'a'
print(d)
i = 1000
print(i)
for i in d{
    print(i+':'+d[i])
}
print('全局 i 未被覆盖')
print(i)
arr = ['1','2','3','4','5']
print(join(arr))
t = join(arr,'A')
print(t)
arr = split(t,'A',3)
print(arr)
arr = split(t,"A")
print(arr)
t = '   \nAlice\n    '
print(t)
print(strip(t))
print(lstrip(t))
print(rstrip(t))
t='Alice!!!0929348abnroiaAlicegohnoiwrAlice'
print(find(t,'Alice',0,10))
print(find(t,'Alice'))
print(find(t,'Alice',20))
# ::是指明使用内置函数
print(::count(t,'Alice',0,10))
print(::count(t,'Alice'))
print(::count(t,'Alice',20))
x = replace(t,'Alice','Mark')
print(x)
x = replace(t,'Alice','Mark',1)
print(x)
x = replace(t,'Alice','Mark',2)
print(x)
print(len(x))
print(len(arr))
y = {}
print(len(y))
y = []
print(len(y))# test
print({})
file = open('mytry.txt','w')
print(file)
write(file,'你好\n')
write(file,'世界\n')
close(file)
file = open('mytry.txt')
txt = read(file)
print(txt)
close(file)
seed(42)
print(random())
print(random())
print(randrange(0,10000))
print(randrange(0,10000))
print('='*120)
try{
    a = 1/0.0

}catch('ZeroDivisionError'){
    print('Zero get')
}finally{
    print('final')
}
remove a
try{
    print(a)
}catch('NameError'){
    print('Name get')
    try{
        remove f
        f()
    }catch('NameError'){
        print('Name get again')
    }
}
a = 10
try{
    try{
        a()
    }catch('TypeError'){
        print('Type get')
    }finally{
        a = [1,2,3]
        try{
            print(a['oiwn'])
        }catch('TypeError'){
            print('Type get again')
        }finally{
            remove a
            a()
        }

    }
}catch('NameError'){
    print('Name here')
}
a = 'oirn'
try{
    a = int(a)
}catch('ValueError'){
    print('Value int')
}

try{
    a = -'str'
}catch('*'){
    print('str')
}
e = 10
print('e is ' + e)
try{
    x = 'str'!
}catch('*') as e{
    print('here')
    vars()
    print(err_name(e))
    print(err_des(e))
}finally{
    print('e is ' + e)
    vars()
}

try{
    throw (0,'自定义错误类型，可以不为字符串')
}catch(0) as e{
    print(err_des(e))
}

try{
    try{
        throw ('my_err', 'des')
    }catch('*') as e{
        throw (-1, err_des(e))
    }
}catch('*') as e{
    print(err_name(e))
    print(err_des(e))
}
try{
    return null
}catch('*') as e{
    print(err_name(e) + ':' + err_des(e))
}
try{
    break
}catch('*') as e{
    print(err_name(e) + ':' + err_des(e))
}
try{
    continue
}catch('*') as e{
    print(err_name(e) + ':' + err_des(e))
}
try{
    if(1){
        return null
    }
    print('if_true')
}catch('*') as e{
    print(err_name(e) + ':' + err_des(e))
}
try{
    if(0){
        return null
    }
    print('if_false')
}catch('*') as e{
    print(err_name(e) + ':' + err_des(e))
}
try{
        while(true){
            if(1){
                break
            }
        }
    print('if_true_while')
}catch('*') as e{
    print(err_name(e) + ':' + err_des(e))
}
try{
    a = {1:'one',2:'two',3:'three'}
    for i in a{
        print(i + ':' + a[i])
        a[4] = 'four'
    }
}catch('*') as e{
    print(err_name(e))
    print(err_des(e))
}
```