library(tidyverse)
dat <- read.csv('data.csv')

dat <- dat %>% filter(Name == "AMD Ryzen™ 7 7700X, Gigabyte B650 Gaming X AX v2, 32GB DDR5")
dat$Discounted.Price = as.numeric(gsub("\\$", "", dat$Discounted.Price))
ggplot(data=dat, aes(x=Time, y=Discounted.Price)) +
  geom_point() + 
  theme_classic()

unique(dat$Name)

for(x in unique(dat$Name)){
  tempdat <- dat %>% filter(Name == x)
  tempdat$Discounted.Price = as.numeric(gsub("\\$", "", tempdat$Discounted.Price))
  
  print(ggplot(data=tempdat, aes(x=Time, y=Discounted.Price)) +
    geom_point() + 
    theme_classic() + 
    ggtitle(Name))
  break;
}

str(dat)
plot(dat$Time, dat$Discounted.Price)

