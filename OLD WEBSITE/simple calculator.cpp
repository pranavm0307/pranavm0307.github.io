#include<simplecpp>

main_program{
cout<<"1. Addition"<<endl<<"2. Subtraction"<<endl<<"3. Multiplication"<<endl<<"4. Division"<<endl<<"enter operator number"<<endl;
double a;
cin>>a;

if(a>4){

cout<<"invalid input!"<<endl;
}
if(a<=4){
double x,y;
cout<<"enter first number"<<endl;
cin>>x;
cout<<"enter second number"<<endl;
cin>>y;
cout<<endl;




if(a==1){
cout<<x+y;
}

if(a==2){
cout<<x-y;
}

if(a==3){
cout<<x*y;
}

if(a==4){
cout<<x/y;
}
}
}