
'use client'
import React, { createContext, useContext, useState } from 'react'
export const StoreContext = createContext<any>(null)
export const StoreProvider: React.FC<{children: React.ReactNode}> = ({children}) => {
  const [conversations, setConversations] = useState([{id:'demo-1', title:'Untitled Chat'}])
  const [currentId, setCurrentId] = useState('demo-1')
  const value = { conversations, currentId, setCurrent:(id:string)=>setCurrentId(id), newChat:()=>setCurrentId('demo-'+Date.now()) }
  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}
export const useStore = () => useContext(StoreContext) as any
